import copy
import os
import sys
from argparse import ArgumentParser
from functools import cache
from pathlib import Path
from typing import Optional

from sw_mc_lib import XMLParserElement, format, parse
from sw_mc_lib.Types import ComponentType

from sw_mc_builder._handling_arguments import parser_arguments
from sw_mc_builder._utils import BUILDER_IDENTIFIER
from sw_mc_builder.microcontroller import Microcontroller


@cache
def get_stormworks_path() -> Path:
    # figure out platform-specific default Steam path
    stormworks_paths: list[Path] = []
    if sys.platform.startswith("win"):
        stormworks_paths = [Path(os.getenv("APPDATA")) / "Stormworks"]
    elif sys.platform.startswith("darwin"):  # macOS
        stormworks_paths = [Path.home() / "Library/Application Support/Stormworks"]
    else:  # Linux and others
        base_paths: set[Path] = {
            (Path.home() / ".steam/steam").resolve(),
            (Path.home() / ".local/share/Steam").resolve(),
        }
        for path in list(base_paths):
            libraryfolders_vdf = path / "steamapps/libraryfolders.vdf"
            if not libraryfolders_vdf.is_file():
                continue
            with libraryfolders_vdf.open() as f:
                while line := f.readline():
                    line = line.strip()
                    if line.startswith('"path"'):
                        # "path"\t\t"/some/path"
                        base_paths.add(Path(line.split("\t")[2].strip('"')).resolve())

        for path in base_paths:
            stormworks_paths.append(
                path
                / "steamapps/compatdata/573090/pfx/drive_c/users/steamuser/AppData/Roaming/Stormworks/"
            )

    stormworks_paths = [p for p in stormworks_paths if p.is_dir()]

    if len(stormworks_paths) == 0:
        raise FileNotFoundError("Could not find Stormworks installation path.")
    if len(stormworks_paths) > 1:
        raise RuntimeError(
            f"Found multiple Stormworks installation paths: {stormworks_paths}"
        )
    return stormworks_paths[0]


def name_to_path(name: str, kind: str) -> Path:
    if name.endswith(".xml"):
        return Path(name).resolve()
    return get_stormworks_path() / f"data/{kind}/{name}.xml"


def extract_mcs_from_vehicle(
    vehicle_path: Path, relevant_names: set[str]
) -> Optional[tuple[XMLParserElement, list[XMLParserElement]]]:
    with vehicle_path.open("r", encoding="utf-8") as f:
        vehicle_xml: XMLParserElement = parse(f.read())
    if vehicle_xml.tag != "vehicle":
        return None
    bodies = vehicle_xml.children[1]
    if bodies.tag != "bodies":
        return None
    relevant_mcs: list[XMLParserElement] = []
    for body in bodies.children:
        if body.tag != "body":
            continue
        components = body.children[0]
        if components.tag != "components":
            continue
        for component in components.children:
            if component.tag != "c":
                continue
            if component.attributes.get("d") != "microprocessor":
                continue
            obj = component.get_child_by_tag("o")
            if obj is None:
                continue
            mc_definition = obj.get_child_by_tag("microprocessor_definition")
            if mc_definition is None:
                continue
            if mc_definition.attributes.get("name") not in relevant_names:
                continue
            group = mc_definition.get_child_by_tag("group")
            if group is None:
                continue
            data = group.get_child_by_tag("data")
            if data is not None and data.attributes.get("desc") == BUILDER_IDENTIFIER:
                relevant_mcs.append(mc_definition)
    return vehicle_xml, relevant_mcs


def find_with_id(
    element: XMLParserElement, component_type: str
) -> list[XMLParserElement]:
    assert element.tag in ("microprocessor", "microprocessor_definition")
    group = element.get_child_by_tag_strict("group")
    components = group.get_child_by_tag_strict("components")
    result: list[XMLParserElement] = []
    for component in components.children:
        if component.attributes.get("type") == component_type:
            result.append(component)
    return result


def find_and_match_property(
    target: XMLParserElement,
    source: XMLParserElement,
    component_type: ComponentType,
) -> list[tuple[XMLParserElement, XMLParserElement]]:
    target_props = find_with_id(target, str(component_type.value))
    source_props = find_with_id(source, str(component_type.value))
    results = []
    for target_prop in target_props:
        target_obj = target_prop.get_child_by_tag_strict("object")
        if target_obj.attributes.get("force_property"):
            continue  # skip properties that are forced to be changed
        prop_name = target_obj.attributes.get("name", target_obj.attributes.get("n"))
        assert prop_name is not None
        for source_prop in source_props:
            source_obj = source_prop.get_child_by_tag_strict("object")
            source_name = source_obj.attributes.get(
                "name", source_obj.attributes.get("n")
            )
            assert source_name is not None
            if prop_name == source_name:
                results.append((target_obj, source_obj))
                break
    return results


def merge_attributes(
    target: XMLParserElement, source: XMLParserElement, attr_name: str
) -> None:
    if attr_name in source.attributes:
        target.attributes[attr_name] = source.attributes[attr_name]
    elif attr_name in target.attributes:
        del target.attributes[attr_name]


def merge_number_properties(
    target: XMLParserElement, source: XMLParserElement, prop_name: str
) -> None:
    target_val = target.get_child_by_tag_strict(prop_name)
    if source_val := source.get_child_by_tag(prop_name):
        target_val.attributes = source_val.attributes


def merge_properties(target: XMLParserElement, source: XMLParserElement) -> None:
    for target_prop, source_prop in find_and_match_property(
        target, source, ComponentType.PropertyText
    ):
        merge_attributes(target_prop, source_prop, "v")
    for target_prop, source_prop in find_and_match_property(
        target, source, ComponentType.PropertyNumber
    ):
        merge_number_properties(target_prop, source_prop, "v")
    for target_prop, source_prop in find_and_match_property(
        target, source, ComponentType.PropertyToggle
    ):
        merge_attributes(target_prop, source_prop, "v")
    for target_prop, source_prop in find_and_match_property(
        target, source, ComponentType.PropertySlider
    ):
        merge_number_properties(target_prop, source_prop, "v")
    for target_prop, source_prop in find_and_match_property(
        target, source, ComponentType.PropertyDropdown
    ):
        possible_values: dict[str, str] = {}
        items = target_prop.get_child_by_tag_strict("items")
        for child in items.children:
            if child.tag == "i":
                possible_values[(child.attributes["l"])] = str(len(possible_values))
        if (source_items := source_prop.get_child_by_tag("items")) and (
            source_index := source_prop.attributes.get("i")
        ):
            if int(source_index) < len(source_items.children):
                source_item = source_items.children[int(source_index)]
                if source_item.tag == "i":
                    label = source_item.attributes.get("l")
                    if label in possible_values:
                        target_prop.attributes["i"] = possible_values[label]


def replace_in_vehicle(
    vehicle_name: str,
    mcs: dict[str, tuple[Microcontroller, XMLParserElement]],
) -> None:
    vehicle_path = name_to_path(vehicle_name, "vehicles")
    if not vehicle_path.is_file():
        print(f'Could not find vehicle file "{vehicle_name}".')
        return
    result = extract_mcs_from_vehicle(vehicle_path, set(mcs.keys()))
    if result is None:
        print(f'Could not parse vehicle file "{vehicle_name}".')
        return
    vehicle_xml, vehicle_mcs = result
    if len(vehicle_mcs) == 0:
        print(f'No microcontrollers to update in vehicle "{vehicle_name}".')
        return
    for vehicle_mc in vehicle_mcs:
        name: str = vehicle_mc.attributes["name"]
        mc_xml: XMLParserElement = copy.deepcopy(mcs[name][1])
        merge_properties(mc_xml, vehicle_mc)
        vehicle_mc.attributes = mc_xml.attributes
        vehicle_mc.children = mc_xml.children
    with vehicle_path.open("w", encoding="utf-8") as f:
        f.write(format(vehicle_xml))
    print(f'Wrote microcontrollers to vehicle "{vehicle_name}".')


def handle_mcs(*mcs: Microcontroller) -> None:
    # pylint: disable=protected-access
    if len(mcs) == 0:
        raise ValueError("At least one microcontroller must be provided")
    parser = ArgumentParser(description="Microcontroller collection")
    parser_arguments(parser)
    args = parser.parse_args()
    if args.select:
        selected_names = {name.strip() for name in args.select.split(",")}
    else:
        selected_names = set()
    compiled: dict[str, tuple[Microcontroller, XMLParserElement]] = {}
    for mc in mcs:
        name: str = mc._mc.name
        if selected_names and not any(
            selected_name in name for selected_name in selected_names
        ):
            continue
        if name in compiled:
            raise ValueError(f"Duplicate microcontroller name: {name}")
        compiled[name] = (mc, mc._resolve_and_optimize())
    if args.microcontroller:
        for name, (mc, xml_mc) in compiled.items():
            mc_path = name_to_path(mc._save_name, "microprocessors")
            mc_path.parent.mkdir(parents=True, exist_ok=True)
            with mc_path.open("w", encoding="utf-8") as f:
                f.write(format(xml_mc))
                print(f'Wrote microcontroller "{name}" to microcontroller directory.')
            mc._mc.image.to_sw_png(mc_path.with_suffix(".png"))
    if args.vehicle:
        for vehicle_name in args.vehicle.split(","):
            replace_in_vehicle(vehicle_name, compiled)
