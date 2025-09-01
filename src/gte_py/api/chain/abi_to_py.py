import json
import os
import re
import keyword
import builtins
from eth_utils.crypto import keccak
from typing import Any

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build paths relative to the script directory
abi_dir = os.path.join(script_dir, "abi")
output_dir = os.path.join(script_dir, ".")
os.makedirs(output_dir, exist_ok=True)

TYPE_MAP = {
    "uint256": "int",
    "uint8": "int",
    "uint": "int",
    "int256": "int",
    "uint96": "int",
    "uint160": "int",
    "uint48": "int",
    "uint32": "int",
    "uint64": "int",
    "address": "ChecksumAddress",
    "bool": "bool",
    "string": "str",
    "bytes": "HexBytes",
    "bytes32": "HexBytes",
}

PRIMITIVE_TYPES = set(TYPE_MAP.keys())

def solidity_to_pytype(sol_type: str, struct_types: set[str] | None = None) -> str:
    if struct_types is None:
        struct_types = set()
    
    if sol_type.endswith("[]"):
        base = sol_type[:-2]
        if base in struct_types:
            return f"list[{base}]"
        return f"list[{TYPE_MAP.get(base, 'Any')}]"
    
    if sol_type in struct_types:
        return sol_type
    
    return TYPE_MAP.get(sol_type, "Any")

def to_pascal_case(s: str) -> str:
    return ''.join(w.capitalize() for w in s.split('_'))

def to_snake_case(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def normalize_param_name(name: str) -> str:
    snake_name = to_snake_case(name)
    # Remove leading underscores for namedtuples
    if snake_name.startswith('_'):
        snake_name = snake_name[1:]
    # Check if it's a Python keyword or builtin
    if keyword.iskeyword(snake_name) or hasattr(builtins, snake_name):
        return snake_name + "_"
    return snake_name

def is_primitive_type(sol_type: str) -> bool:
    if sol_type.endswith("[]"):
        return False
    return sol_type in PRIMITIVE_TYPES

def extract_struct_name(internal_type: str) -> str | None:
    """Extract struct name from internalType like 'struct ICLOB.CancelArgs'"""
    if internal_type and internal_type.startswith("struct "):
        parts = internal_type.split(".")
        if len(parts) > 1:
            return parts[-1]  # Take the last part (e.g., "CancelArgs")
        else:
            return internal_type.replace("struct ", "")
    return None

def generate_struct_class(struct_name: str, components: list[dict[str, Any]], struct_types: set[str]) -> str:
    """Generate a NamedTuple class for a struct"""
    lines = [f'class {struct_name}(NamedTuple):']
    lines.append(f'    """Struct definition for {struct_name}."""')
    lines.append("")
    
    for component in components:
        name = normalize_param_name(component["name"] or "param")
        sol_type = component["type"]
        
        # Handle struct types
        if sol_type == "tuple" and component.get("components"):
            nested_struct_name = extract_struct_name(component.get("internalType", ""))
            if nested_struct_name:
                py_type = nested_struct_name
            else:
                py_type = "Any"
        # Handle arrays
        elif sol_type.endswith("[]"):
            base_type = sol_type[:-2]
            if base_type in struct_types:
                py_type = f"list[{base_type}]"
            else:
                py_type = f"list[{TYPE_MAP.get(base_type, 'Any')}]"
        # Handle regular types
        else:
            py_type = TYPE_MAP.get(sol_type, "Any")
        
        lines.append(f"    {name}: {py_type}")
    
    return '\n'.join(lines)

def extract_all_structs_from_abis(abi_files: list[str]) -> dict[str, str]:
    """Extract all unique struct definitions from all ABIs"""
    all_structs = {}
    struct_types = set()
    
    # First pass: collect all struct names from all ABIs
    for abi_file in abi_files:
        with open(abi_file, "r") as f:
            abi = json.load(f)
        
        # Check if this is perp_manager ABI
        is_perp_manager = "perp_manager.json" in abi_file
        
        def process_type(type_info):
            if type_info.get("type") == "tuple" and type_info.get("components"):
                struct_name = extract_struct_name(type_info.get("internalType", ""))
                if struct_name:
                    # Append "Perp" suffix for perp_manager structs
                    if is_perp_manager:
                        struct_name += "Perp"
                    struct_types.add(struct_name)
                    # Recursively process nested structs
                    for component in type_info["components"]:
                        process_type(component)
        
        for item in abi:
            if item.get("type") == "function":
                for inp in item.get("inputs", []):
                    process_type(inp)
                for out in item.get("outputs", []):
                    process_type(out)
            elif item.get("type") == "event":
                for inp in item.get("inputs", []):
                    process_type(inp)
    
    # Second pass: generate struct definitions
    for abi_file in abi_files:
        with open(abi_file, "r") as f:
            abi = json.load(f)
        
        # Check if this is perp_manager ABI
        is_perp_manager = "perp_manager.json" in abi_file
        
        def generate_struct_definitions(type_info):
            if type_info.get("type") == "tuple" and type_info.get("components"):
                struct_name = extract_struct_name(type_info.get("internalType", ""))
                if struct_name:
                    # Append "Perp" suffix for perp_manager structs
                    final_struct_name = struct_name + "Perp" if is_perp_manager else struct_name
                    if final_struct_name not in all_structs:
                        # Generate nested structs first
                        for component in type_info["components"]:
                            generate_struct_definitions(component)
                        # Generate this struct
                        all_structs[final_struct_name] = generate_struct_class(final_struct_name, type_info["components"], struct_types)
        
        for item in abi:
            if item.get("type") == "function":
                for inp in item.get("inputs", []):
                    generate_struct_definitions(inp)
                for out in item.get("outputs", []):
                    generate_struct_definitions(out)
            elif item.get("type") == "event":
                for inp in item.get("inputs", []):
                    generate_struct_definitions(inp)
    
    return all_structs

def get_structs_used_by_abi(abi: list[dict[str, Any]]) -> set[str]:
    """Get all struct names used by this ABI"""
    structs_used = set()
    
    def process_type(type_info):
        if type_info.get("type") == "tuple" and type_info.get("components"):
            struct_name = extract_struct_name(type_info.get("internalType", ""))
            if struct_name:
                structs_used.add(struct_name)
                # Recursively process nested structs
                for component in type_info["components"]:
                    process_type(component)
    
    for item in abi:
        if item.get("type") == "function":
            for inp in item.get("inputs", []):
                process_type(inp)
            for out in item.get("outputs", []):
                process_type(out)
        elif item.get("type") == "event":
            for inp in item.get("inputs", []):
                process_type(inp)
    
    return structs_used

def get_perp_structs_used_by_abi(abi: list[dict[str, Any]]) -> set[str]:
    """Get all struct names used by PerpManager ABI with 'Perp' suffix"""
    structs_used = set()
    
    def process_type(type_info):
        if type_info.get("type") == "tuple" and type_info.get("components"):
            struct_name = extract_struct_name(type_info.get("internalType", ""))
            if struct_name:
                # Append 'Perp' to avoid conflicts with CLOB structs
                structs_used.add(struct_name + "Perp")
                # Recursively process nested structs
                for component in type_info["components"]:
                    process_type(component)
    
    for item in abi:
        if item.get("type") == "function":
            for inp in item.get("inputs", []):
                process_type(inp)
            for out in item.get("outputs", []):
                process_type(out)
        elif item.get("type") == "event":
            for inp in item.get("inputs", []):
                process_type(inp)
    
    return structs_used

def generate_event_class(event: dict[str, Any], struct_types: set[str]) -> tuple[str, str]:
    # Ensure event class name is UpperCamelCase (PascalCase) and matches event name exactly
    pascal_name = event['name'] + "Event"
    lines = [f"@dataclass", f"class {pascal_name}:"]
    for inp in event.get('inputs', []):
        if inp.get("type") == "tuple" and inp.get("components"):
            # This is a struct - use the struct name as the type
            struct_name = extract_struct_name(inp.get("internalType", ""))
            if struct_name:
                typ = struct_name
            else:
                typ = "Any"
        else:
            typ = solidity_to_pytype(inp['type'], struct_types)
        name = normalize_param_name(inp['name'] or 'param')
        lines.append(f"    {name}: {typ}")
    return '\n'.join(lines), pascal_name

def build_error_selector_map(abi: list[dict[str, Any]]) -> dict[str, str]:
    """Build a map from error selector (hex string) to error signature"""
    error_map = {}
    for item in abi:
        if item.get("type") == "error":
            name = item["name"]
            types = ",".join([input_item["type"] for input_item in item.get("inputs", [])])
            signature = f"{name}({types})"
            selector = "0x" + keccak(text=signature)[:4].hex()
            error_map[selector] = signature
    return error_map

def extract_all_errors_from_abis(abi_files: list[str]) -> dict[str, str]:
    """Extract all unique error selectors from all ABIs"""
    all_errors = {}
    
    for abi_file in abi_files:
        with open(abi_file, "r") as f:
            abi = json.load(f)
        
        error_map = build_error_selector_map(abi)
        all_errors.update(error_map)  # Merge into the overall map
    
    return all_errors

def extract_enum_name(internal_type: str) -> str | None:
    """Extract enum name from internalType like 'enum Side' or 'enum ICLOB.LimitOrderType'"""
    if internal_type and internal_type.startswith("enum "):
        enum_part = internal_type.replace("enum ", "")
        # Handle qualified names like "ICLOB.LimitOrderType" 
        if "." in enum_part:
            return enum_part.split(".")[-1]  # Take the last part
        return enum_part
    return None

def extract_all_enums_from_abis(abi_files: list[str]) -> set[str]:
    """Extract all unique enum names from all ABIs"""
    all_enums = set()
    
    for abi_file in abi_files:
        with open(abi_file, "r") as f:
            abi = json.load(f)
        
        def process_type(type_info):
            # Check if this is an enum (type is uint8 but internalType is enum)
            if (type_info.get("type") == "uint8" and 
                type_info.get("internalType", "").startswith("enum ")):
                enum_name = extract_enum_name(type_info.get("internalType", ""))
                if enum_name:
                    all_enums.add(enum_name)
            
            # Process nested components for structs
            if type_info.get("type") == "tuple" and type_info.get("components"):
                for component in type_info["components"]:
                    process_type(component)
        
        for item in abi:
            if item.get("type") == "function":
                for inp in item.get("inputs", []):
                    process_type(inp)
                for out in item.get("outputs", []):
                    process_type(out)
            elif item.get("type") == "event":
                for inp in item.get("inputs", []):
                    process_type(inp)
    
    return all_enums

def generate_enums_template(enum_names: set[str]) -> str:
    """Generate a template for enum definitions"""
    lines = ["# This file is auto-generated template. Fill in the enum values manually."]
    lines.append("from enum import IntEnum")
    lines.append("")
    
    for enum_name in sorted(enum_names):
        lines.append(f"class {enum_name}(IntEnum):")
        lines.append(f"    # TODO: Add actual enum values for {enum_name}")
        lines.append(f"    # Example: VALUE_NAME = 0")
        lines.append("    pass")
        lines.append("")
    
    return "\n".join(lines)

def generate_output_type(outputs, fn_name, contract_name=None, struct_types=None):
    if struct_types is None:
        struct_types = set()
    
    if not outputs:
        return "Any", None, None
    if len(outputs) == 1:
        output = outputs[0]
        if output.get("type") == "tuple" and output.get("components"):
            # This is a struct output
            struct_name = extract_struct_name(output.get("internalType", ""))
            if struct_name:
                # For PerpManager, append "Perp" to struct names
                if contract_name == "perp_manager":
                    typ = struct_name + "Perp"
                else:
                    typ = struct_name
            else:
                typ = "Any"
        else:
            typ = solidity_to_pytype(output["type"], struct_types)
        return typ, None, [output.get("name") or f"{fn_name}_result0"]
    # Multiple outputs: use tuple with field names for documentation
    # Build a tuple type hint using TYPE_MAP for each output
    tuple_types = []
    for out in outputs:
        if out.get("type") == "tuple" and out.get("components"):
            # This is a struct output
            struct_name = extract_struct_name(out.get("internalType", ""))
            if struct_name:
                # For PerpManager, append "Perp" to struct names
                if contract_name == "perp_manager":
                    tuple_types.append(struct_name + "Perp")
                else:
                    tuple_types.append(struct_name)
            else:
                tuple_types.append("Any")
        else:
            sol_type = out["type"]
            tuple_types.append(TYPE_MAP.get(sol_type, "Any"))
    tuple_type_hint = f"tuple[{', '.join(tuple_types)}]"
    fields = [normalize_param_name(out.get("name") or f"{fn_name}_result{idx}") for idx, out in enumerate(outputs)]
    return tuple_type_hint, None, fields

def generate_contract_class(abi: list[dict[str, Any]], class_name: str, event_class_names: list[str], struct_types: set[str], contract_name: str) -> str:
    imports = ["# This file is auto-generated. Do not edit manually."]
    imports.append("from typing import Any")
    imports.append("from .utils import TypedContractFunction, load_abi")
    imports.append("from eth_typing import ChecksumAddress")
    imports.append("from web3 import AsyncWeb3")
    imports.append("from hexbytes import HexBytes")
    
    # Import structs used by this ABI
    if contract_name == "perp_manager":
        structs_used = get_perp_structs_used_by_abi(abi)
    else:
        structs_used = get_structs_used_by_abi(abi)
    
    if structs_used:
        imports.append(f"from .structs import {', '.join(sorted(structs_used))}")
    
    if event_class_names:
        imports.append(f"from .events import {', '.join(sorted(event_class_names))}")
    
    methods = []

    for item in abi:
        if item["type"] == "constructor":
            # Skip constructor - we don't need namedtuples for constructor inputs
            pass
        elif item["type"] == "function":
            fn_name = item["name"]
            snake_fn = to_snake_case(fn_name)
            pascal_fn = to_pascal_case(fn_name)
            inputs = item.get("inputs", [])
            outputs = item.get("outputs", [])
            is_view = item.get("stateMutability") in ("view", "pure")
            
            # Output type
            ret_type, tuple_fields, output_field_names = generate_output_type(outputs, snake_fn, contract_name, struct_types)
            # No more namedtuples - field names will be used in docstring
            
            # Method signature
            sig_args = []
            doc_args = []
            py_arg_names = []
            contract_arg_names = []
            struct_args = []  # Track which args are structs
            
            for inp in inputs:
                if inp.get("type") == "tuple" and inp.get("components"):
                    # This is a struct - use the struct name as the type
                    struct_name = extract_struct_name(inp.get("internalType", ""))
                    if struct_name:
                        # For PerpManager, append "Perp" to struct names to match our naming convention
                        if contract_name == "perp_manager":
                            typ = struct_name + "Perp"
                        else:
                            typ = struct_name
                        struct_args.append(True)
                    else:
                        typ = "Any"
                        struct_args.append(False)
                else:
                    # Regular type
                    typ = solidity_to_pytype(inp["type"], struct_types)
                    struct_args.append(False)
                
                orig_name = inp["name"] or "param"
                py_name = orig_name[1:] if orig_name.startswith('_') else orig_name
                py_name = normalize_param_name(py_name)
                sig_args.append(f"{py_name}: {typ}")
                doc_args.append(f"{py_name}: {typ}")
                py_arg_names.append(py_name)
                contract_arg_names.append(orig_name)
            
            # Add **kwargs for non-view functions
            if not is_view:
                sig_args.append("**kwargs")
            
            # Method definition
            method_sig = f"    {'async ' if is_view else ''}def {snake_fn}(self"
            if sig_args:
                method_sig += ", " + ", ".join(sig_args)
            # For async view functions with multiple outputs, use the tuple type hint
            if is_view and ret_type.startswith('tuple['):
                method_sig += f") -> {ret_type}:"
            else:
                method_sig += f") -> {ret_type if is_view else 'TypedContractFunction[Any]'}:"
            
            method_lines = [method_sig]
            
            # Add docstring if there are multiple outputs to explain tuple elements
            if output_field_names and len(output_field_names) > 1:
                docstring = '        """'
                if is_view:
                    docstring += f'\n        Returns:\n            tuple: ('
                    docstring += ', '.join(output_field_names) + ')'
                else:
                    docstring += f'\n        Returns:\n            TypedContractFunction that returns tuple: ('
                    docstring += ', '.join(output_field_names) + ')'
                docstring += '\n        """'
                method_lines.append(docstring)
            
            # Function body
            if py_arg_names:
                # Convert struct args to tuples and prepare call args
                call_args = []
                for i, (py_name, is_struct) in enumerate(zip(py_arg_names, struct_args)):
                    if is_struct:
                        call_args.append(f"tuple({py_name})")
                    else:
                        call_args.append(py_name)
                
                call_args_str = ', '.join(call_args)
                method_lines.append(f"        func = self.contract.functions.{fn_name}({call_args_str})")
            else:
                method_lines.append(f"        func = self.contract.functions.{fn_name}()")
            
            if is_view:
                # For view functions, call immediately and return result
                method_lines.append(f"        return await func.call()")
            else:
                # For non-view functions, return TypedContractFunction
                method_lines.append(f"        return TypedContractFunction(func, params={{**kwargs}})")
            
            methods.append('\n'.join(method_lines))

    # Imports
    lines = imports + ["", ""]
    
    # Contract class
    lines.append(f'class {class_name}:')
    lines.append(f'    def __init__(self, web3: AsyncWeb3, address: ChecksumAddress):')
    lines.append(f'        self.web3 = web3')
    lines.append(f'        self.address = address')
    lines.append(f'        loaded_abi = load_abi("{contract_name}")')
    lines.append(f'        self.contract = web3.eth.contract(address=address, abi=loaded_abi)')
    lines.append("")
    
    # Add methods with blank lines between them
    for i, method in enumerate(methods):
        lines.append(method)
        if i < len(methods) - 1:  # Don't add blank line after last method
            lines.append("")
    
    return '\n'.join(lines)

# --- Batch processing for all ABI files in abi/ directory ---
# Find all .json files in abi_dir
abi_files = [os.path.join(abi_dir, f) for f in os.listdir(abi_dir) if f.endswith('.json')]

# Extract all structs from all ABIs and write to structs.py
all_structs = extract_all_structs_from_abis(abi_files)

# Extract all enums from all ABIs 
all_enums = extract_all_enums_from_abis(abi_files)

with open(os.path.join(output_dir, "structs.py"), "w") as f:
    f.write("# This file is auto-generated. Do not edit manually.\n")
    f.write("from typing import NamedTuple, Any\n")
    f.write("from eth_typing import ChecksumAddress\n")
    f.write("from hexbytes import HexBytes\n")
    f.write("from enum import IntEnum\n")
    f.write("\n")
    
    # Write enums first
    if all_enums:
        f.write("# Enums\n")
        for enum_name in sorted(all_enums):
            f.write(f"class {enum_name}(IntEnum):\n")
            f.write(f"    # TODO: Add actual enum values for {enum_name}\n")
            f.write(f"    # Example: VALUE_NAME = 0\n")
            f.write("    pass\n")
            f.write("\n")
        f.write("\n")
    
    # Write structs
    f.write("# Structs\n")
    for struct_name in sorted(all_structs.keys()):
        f.write(all_structs[struct_name] + "\n\n")

# Extract all errors from all ABIs and write to errors.py
all_errors = extract_all_errors_from_abis(abi_files)
with open(os.path.join(output_dir, "errors.py"), "w") as f:
    f.write("# This file is auto-generated. Do not edit manually.\n")
    f.write("# Error selector to signature mapping\n")
    f.write("ERROR_SELECTORS = {\n")
    for selector in sorted(all_errors.keys()):  # Sort for consistent output
        signature = all_errors[selector]
        f.write(f'    "{selector}": "{signature}",\n')
    f.write("}\n")

# Extract all enums from all ABIs and write to enums.py template
# all_enums = extract_all_enums_from_abis(abi_files)
# with open(os.path.join(output_dir, "enums.py"), "w") as f:
#     f.write(generate_enums_template(all_enums))

# Collect all events from all ABIs
all_events = {}
abi_event_map = {}  # Map: abi_file -> set of event class names
events_struct_usage = set()  # Track which structs are used by events

# First pass: collect all unique events
struct_types = set(all_structs.keys())
for abi_file in abi_files:
    with open(abi_file, "r") as f:
        abi = json.load(f)
    event_class_names = set()
    for item in abi:
        if item.get("type") == "event":
            # Check if this event uses any structs
            for inp in item.get('inputs', []):
                if inp.get("type") == "tuple" and inp.get("components"):
                    struct_name = extract_struct_name(inp.get("internalType", ""))
                    if struct_name:
                        events_struct_usage.add(struct_name)
            
            event_class, class_name = generate_event_class(item, struct_types)
            all_events[class_name] = event_class  # Will overwrite duplicates, which is fine
            event_class_names.add(class_name)
    abi_event_map[abi_file] = event_class_names

# Write all event classes to events.py
with open(os.path.join(output_dir, "events.py"), "w") as f:
    f.write("# This file is auto-generated. Do not edit manually.\n")
    f.write("from dataclasses import dataclass\n")
    f.write("from eth_typing import ChecksumAddress\n")
    f.write("from hexbytes import HexBytes\n")
    # Import structs used by events
    if events_struct_usage:
        f.write(f"from .structs import {', '.join(sorted(events_struct_usage))}\n")
    f.write("\n")
    for class_name in sorted(all_events.keys()):  # Sort for consistent output
        f.write(all_events[class_name] + "\n\n")

# Generate a wrapper for each ABI
struct_types = set(all_structs.keys())
for abi_file in abi_files:
    with open(abi_file, "r") as f:
        abi = json.load(f)
    base = os.path.splitext(os.path.basename(abi_file))[0]
    py_file = base + ".py"
    class_name = to_pascal_case(base)
    event_class_names = abi_event_map[abi_file]
    generated_code = generate_contract_class(abi, class_name, event_class_names, struct_types, base)
    with open(os.path.join(output_dir, py_file), "w") as f:
        f.write(generated_code)