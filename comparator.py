import yaml
from typing import Any, Dict, List, Optional, Union

class DiffResult:
    def __init__(self):
        self.info_changes = {}
        self.new_paths = []
        self.removed_paths = []
        self.modified_paths = {}
        self.new_components = {}
        self.removed_components = {}
        self.modified_components = {}
        self.renamed_components = {}
        self.tags_changes = {}
        self.servers_changes = {}

def load_yaml(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

import os

def compare_specs(old_spec: Dict[str, Any], new_spec: Dict[str, Any], debug_mode: bool = False) -> DiffResult:
    # DEBUG LOGGING
    if debug_mode:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        with open(os.path.join(log_dir, "comparator_debug.log"), "w") as f:
            f.write("Starting comparison...\n")
            f.write(f"Old Spec Keys: {list(old_spec.keys())}\n")
            f.write(f"New Spec Keys: {list(new_spec.keys())}\n")

        # DEBUG: Dump full specs to analyze structure
        with open(os.path.join(log_dir, "debug_old_spec.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(old_spec, f)
        with open(os.path.join(log_dir, "debug_new_spec.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(new_spec, f)

    result = DiffResult()
    
    # Compare Info
    _compare_info(old_spec.get('info', {}), new_spec.get('info', {}), result)
    
    # Compare Paths
    _compare_paths(old_spec.get('paths', {}), new_spec.get('paths', {}), result)
    
    # Compare Tags
    _compare_tags(old_spec.get('tags', []), new_spec.get('tags', []), result)
    
    # Compare Servers
    _compare_servers(old_spec.get('servers', []), new_spec.get('servers', []), result)

    # Compare Components
    _compare_components(old_spec.get('components', {}), new_spec.get('components', {}), result)

    # Detect Renamed Components (Iterative Propagation for schemas, Content-based for others)
    _detect_renamed_components(result, old_spec, new_spec)

    # Dump Debug Trees for User Analysis
    if debug_mode:
        _dump_debug_trees(result, old_spec, new_spec)

        with open(os.path.join("logs", "comparator_debug.log"), "a") as f:
            f.write(f"Comparison complete.\n")
            f.write(f"Info Changes: {len(result.info_changes)}\n")
            f.write(f"New Paths: {len(result.new_paths)}\n")
            f.write(f"Modified Paths: {len(result.modified_paths)}\n")
            f.write(f"New Schemas: {len(result.new_components.get('schemas', []))}\n")
            f.write(f"Removed Schemas: {len(result.removed_components.get('schemas', []))}\n")
            f.write(f"Renamed Schemas: {len(result.renamed_components.get('schemas', {}))}\n")

    return result

def _dump_debug_trees(result, old_spec, new_spec):
    """
    Generates a log file showing the full ancestry of unmatched schemas.
    Traces paths back to Endpoints (Roots) to diagnose broken chains.
    """
    def build_parent_map(spec):
        parents = {} # child_name -> list of (parent_name, type)
        
        def register(child_ref, parent_name, parent_type):
            if child_ref.startswith('#/components/schemas/'):
                child = child_ref.split('/')[-1]
                if child not in parents: parents[child] = []
                parents[child].append((parent_name, parent_type))

        def walk(data, context_name, context_type):
            if isinstance(data, dict):
                if '$ref' in data and isinstance(data['$ref'], str):
                    register(data['$ref'], context_name, context_type)
                
                for k, v in data.items():
                    new_name = context_name
                    new_type = context_type
                    
                    if context_type == 'ROOT':
                        if k == 'paths': 
                            new_type = 'PATHS_ROOT'
                        elif k == 'components': 
                            new_type = 'COMPONENTS_ROOT'
                    elif context_type == 'COMPONENTS_ROOT' and k == 'schemas':
                        new_type = 'SCHEMAS_ROOT'
                    elif context_type == 'SCHEMAS_ROOT':
                        new_name = k
                        new_type = 'SCHEMA'
                    elif context_type == 'PATHS_ROOT':
                        new_name = k
                        new_type = 'PATH'
                    
                    walk(v, new_name, new_type)
            elif isinstance(data, list):
                for item in data:
                    walk(item, context_name, context_type)

        walk(spec, 'ROOT', 'ROOT')
        return parents

    old_parents = build_parent_map(old_spec)
    new_parents = build_parent_map(new_spec)

    def get_ancestry_paths(schema_name, parent_map, visited=None):
        if visited is None: visited = set()
        if schema_name in visited: return [] # Cycle detection
        visited.add(schema_name)
        
        direct_parents = parent_map.get(schema_name, [])
        if not direct_parents:
            return [[(schema_name, 'ORPHAN')]]
            
        paths = []
        for p_name, p_type in direct_parents:
            if p_type == 'PATH':
                paths.append([(schema_name, 'SCHEMA'), (p_name, 'ENDPOINT')])
            elif p_type == 'SCHEMA':
                parent_paths = get_ancestry_paths(p_name, parent_map, visited.copy())
                for pp in parent_paths:
                    paths.append([(schema_name, 'SCHEMA')] + pp)
            else:
                paths.append([(schema_name, 'SCHEMA'), (p_name, p_type)])
        return paths

    log_path = os.path.join("logs", "schema_tree_debug.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== SCHEMA ANCESTRY DEBUG ===\n")
        f.write("Tracing paths from Unmatched Schemas back to Endpoints.\n\n")

        def log_ancestry(schemas, parent_map, label):
            f.write(f"--- {label} ---\n")
            for s in sorted(schemas):
                f.write(f"Schema: {s}\n")
                paths = get_ancestry_paths(s, parent_map)
                if not paths:
                    f.write("  (No parents found)\n")
                else:
                    count = 0
                    for p in paths:
                        if count > 5: 
                            f.write("  ... (more paths truncated)\n")
                            break
                        # Format: Endpoint -> Parent -> Child
                        chain = " -> ".join([f"{name} ({type})" for name, type in reversed(p)])
                        f.write(f"  Path: {chain}\n")
                        count += 1
                f.write("\n")
def _compare_tags(old_tags: List, new_tags: List, result: DiffResult):
    old_t = {t['name']: t for t in old_tags}
    new_t = {t['name']: t for t in new_tags}
    
    diff = _compare_dict_items(old_t, new_t, lambda o, n: {'old': o, 'new': n} if o != n else {})
    if diff:
        result.tags_changes = diff # Need to add this field to DiffResult

def _compare_servers(old_servers: List, new_servers: List, result: DiffResult):
    # Simplified server comparison (by url)
    old_s = {s['url']: s for s in old_servers}
    new_s = {s['url']: s for s in new_servers}
    
    diff = _compare_dict_items(old_s, new_s, lambda o, n: {'old': o, 'new': n} if o != n else {})
    if diff:
        result.servers_changes = diff # Need to add this field to DiffResult

def _is_effectively_equal(v1: Any, v2: Any) -> bool:
    if v1 == v2:
        return True
    if isinstance(v1, str) and isinstance(v2, str):
        # Aggressive normalization:
        # 1. Normalize line endings to \n
        # 2. Strip trailing whitespace from EACH line
        # 3. Strip leading/trailing newlines/whitespace from the whole block
        def normalize(s):
            lines = s.replace('\r\n', '\n').split('\n')
            return "\n".join([line.rstrip() for line in lines]).strip()
            
        return normalize(v1) == normalize(v2)
    return False

def _compare_extensions(old_data: Dict, new_data: Dict) -> Dict:
    """Finds changes in keys starting with x-"""
    diff = {}
    old_ext = {k: v for k, v in old_data.items() if k.startswith('x-')}
    new_ext = {k: v for k, v in new_data.items() if k.startswith('x-')}
    
    all_keys = set(old_ext.keys()) | set(new_ext.keys())
    for k in all_keys:
        v1 = old_ext.get(k)
        v2 = new_ext.get(k)
        if not _is_effectively_equal(v1, v2):
            diff[k] = {'old': v1, 'new': v2}
    return diff

def _compare_info(old_info: Dict, new_info: Dict, result: DiffResult):
    for key in ['title', 'version', 'description', 'termsOfService', 'contact', 'license']:
        old_val = old_info.get(key)
        new_val = new_info.get(key)
        if not _is_effectively_equal(old_val, new_val):
            result.info_changes[key] = {'old': old_val, 'new': new_val}

def _compare_paths(old_paths: Dict, new_paths: Dict, result: DiffResult):
    old_keys = set(old_paths.keys())
    new_keys = set(new_paths.keys())
    
    result.new_paths = list(new_keys - old_keys)
    result.removed_paths = list(old_keys - new_keys)
    
    for path in old_keys & new_keys:
        path_diff = _compare_path_item(old_paths[path], new_paths[path])
        if path_diff:
            result.modified_paths[path] = path_diff

def _compare_path_item(old_item: Dict, new_item: Dict) -> Dict:
    diff = {}
    # Compare operations (get, post, etc.)
    ops = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']
    
    for op in ops:
        if op in old_item and op not in new_item:
            diff.setdefault('removed_ops', []).append(op)
        elif op not in old_item and op in new_item:
            diff.setdefault('new_ops', []).append(op)
        elif op in old_item and op in new_item:
            op_diff = _compare_operation(old_item[op], new_item[op])
            if op_diff:
                diff.setdefault('modified_ops', {})[op] = op_diff
                
    return diff

def _compare_operation(old_op: Dict, new_op: Dict) -> Dict:
    diff = {}
    
    # Compare Metadata (summary, description, deprecated, operationId)
    for key in ['summary', 'description', 'deprecated', 'operationId']:
        if not _is_effectively_equal(old_op.get(key), new_op.get(key)):
            diff[key] = {'old': old_op.get(key), 'new': new_op.get(key)}

    # Custom Extensions
    ext_diff = _compare_extensions(old_op, new_op)
    if ext_diff: diff.update(ext_diff)

    # Compare Parameters
    old_params = {p.get('name'): p for p in old_op.get('parameters', [])}
    new_params = {p.get('name'): p for p in new_op.get('parameters', [])}
    
    params_diff = _compare_dict_items(old_params, new_params, _compare_parameter)
    if params_diff:
        diff['parameters'] = params_diff

    # Compare Request Body
    if 'requestBody' in old_op or 'requestBody' in new_op:
        rb_diff = _compare_request_body(old_op.get('requestBody', {}), new_op.get('requestBody', {}))
        if rb_diff:
            diff['requestBody'] = rb_diff

    # Compare Responses
    old_responses = old_op.get('responses', {})
    new_responses = new_op.get('responses', {})
    responses_diff = _compare_dict_items(old_responses, new_responses, _compare_response)
    if responses_diff:
        diff['responses'] = responses_diff
        
    return diff

def _compare_parameter(old_param: Dict, new_param: Dict) -> Dict:
    diff = {}
    # Check basic fields
    for key in ['in', 'required', 'description', 'deprecated']:
        if not _is_effectively_equal(old_param.get(key), new_param.get(key)):
            diff[key] = {'old': old_param.get(key), 'new': new_param.get(key)}
            
    # Check schema
    if 'schema' in old_param or 'schema' in new_param:
        schema_diff = _compare_schema(old_param.get('schema', {}), new_param.get('schema', {}))
        if schema_diff:
            diff['schema'] = schema_diff
            
    # Custom Extensions
    ext_diff = _compare_extensions(old_param, new_param)
    if ext_diff: diff.update(ext_diff)

    return diff

def _compare_request_body(old_rb: Dict, new_rb: Dict) -> Dict:
    diff = {}
    if old_rb.get('required') != new_rb.get('required'):
        diff['required'] = {'old': old_rb.get('required'), 'new': new_rb.get('required')}
        
    # Compare Content
    old_content = old_rb.get('content', {})
    new_content = new_rb.get('content', {})
    content_diff = _compare_dict_items(old_content, new_content, _compare_media_type)
    if content_diff:
        diff['content'] = content_diff

    # Custom Extensions
    ext_diff = _compare_extensions(old_rb, new_rb)
    if ext_diff: diff.update(ext_diff)
        
    return diff

def _compare_response(old_resp: Dict, new_resp: Dict) -> Dict:
    diff = {}
    if not _is_effectively_equal(old_resp.get('description'), new_resp.get('description')):
        diff['description'] = {'old': old_resp.get('description'), 'new': new_resp.get('description')}
        
    # Compare Content
    old_content = old_resp.get('content', {})
    new_content = new_resp.get('content', {})
    content_diff = _compare_dict_items(old_content, new_content, _compare_media_type)
    if content_diff:
        diff['content'] = content_diff

    # Custom Extensions
    ext_diff = _compare_extensions(old_resp, new_resp)
    if ext_diff: diff.update(ext_diff)
        
    return diff

def _compare_media_type(old_mt: Dict, new_mt: Dict) -> Dict:
    diff = {}
    if 'schema' in old_mt or 'schema' in new_mt:
        schema_diff = _compare_schema(old_mt.get('schema', {}), new_mt.get('schema', {}))
        if schema_diff:
            diff['schema'] = schema_diff
            
    # Compare Examples
    old_exs = old_mt.get('examples', {})
    new_exs = new_mt.get('examples', {})
    exs_diff = _compare_dict_items(old_exs, new_exs, _compare_example)
    if exs_diff:
        diff['examples'] = exs_diff
    elif not _is_effectively_equal(old_mt.get('example'), new_mt.get('example')):
        # Fallback to single 'example' field
        diff['example'] = {'old': old_mt.get('example'), 'new': new_mt.get('example')}
        
    # Compare Encoding
    if not _is_effectively_equal(old_mt.get('encoding'), new_mt.get('encoding')):
        diff['encoding'] = {'old': old_mt.get('encoding'), 'new': new_mt.get('encoding')}

    # Custom Extensions
    ext_diff = _compare_extensions(old_mt, new_mt)
    if ext_diff: diff.update(ext_diff)
    
    return diff

def _compare_dict_items(old_dict: Dict, new_dict: Dict, item_comparator) -> Dict:
    diff = {}
    old_keys = set(old_dict.keys())
    new_keys = set(new_dict.keys())
    
    new_items = list(new_keys - old_keys)
    removed_items = list(old_keys - new_keys)
    
    if new_items: diff['new'] = new_items
    if removed_items: diff['removed'] = removed_items
    
    for key in old_keys & new_keys:
        item_diff = item_comparator(old_dict[key], new_dict[key])
        if item_diff:
            diff.setdefault('modified', {})[key] = item_diff
            
    return diff

def _compare_components(old_comps: Dict, new_comps: Dict, result: DiffResult):
    # Compare all component types
    component_types = {
        'schemas': _compare_schema,
        'parameters': _compare_parameter,
        'responses': _compare_response,
        'requestBodies': _compare_request_body,
        'securitySchemes': _compare_security_scheme,
        'headers': _compare_header,
        'links': _compare_link,
        'callbacks': _compare_callback,
        'examples': _compare_example
    }

    for comp_type, comparator in component_types.items():
        old_items = old_comps.get(comp_type, {})
        new_items = new_comps.get(comp_type, {})
        
        diff = _compare_dict_items(old_items, new_items, comparator)
        if diff:
            result.new_components[comp_type] = diff.get('new', [])
            result.removed_components[comp_type] = diff.get('removed', [])
            result.modified_components[comp_type] = diff.get('modified', {})

def _detect_renamed_components(result: DiffResult, old_spec: Dict, new_spec: Dict):
    """
    Generalized Rename Detection for all component types.
    """
    comp_types = ['schemas', 'parameters', 'responses', 'headers', 'securitySchemes', 'examples', 'links', 'callbacks']
    
    for c_type in comp_types:
        if c_type == 'schemas':
            # Schemas use the complex iterative propagation logic
            _detect_renamed_type_logic(result, old_spec, new_spec, c_type, _compare_schema, _is_deeply_identical, use_propagation=True)
        elif c_type == 'examples':
            # Examples use content-based matching (ignoring summary if it matches key)
            def is_ex_identical(o, n):
                # Ignore summary for "Rename" identification if everything else matches
                for k in ['description', 'value', 'externalValue']:
                    if not _is_effectively_equal(o.get(k), n.get(k)): return False
                return True
            _detect_renamed_type_logic(result, old_spec, new_spec, c_type, _compare_example, is_ex_identical, use_propagation=False)
        else:
            # Generic matching for others
            # The comparator function for a type 'X' is typically '_compare_X'.
            # For 'parameters', it's '_compare_parameter'. For 'responses', '_compare_response', etc.
            # The component type names are plural, so we need to remove the 's' for the function name.
            # Special case for 'requestBodies' -> '_compare_request_body'
            comparator_name = f'_compare_{c_type[:-1]}' if c_type != 'requestBodies' else '_compare_request_body'
            comparator = globals().get(comparator_name, lambda o,n: {})
            _detect_renamed_type_logic(result, old_spec, new_spec, c_type, comparator, lambda o,n: o == n, use_propagation=False)

def _detect_renamed_type_logic(result: DiffResult, old_spec: Dict, new_spec: Dict, comp_type: str, item_comparator, content_matcher, use_propagation=False):
    removed = set(result.removed_components.get(comp_type, []))
    new = set(result.new_components.get(comp_type, []))
    
    if not removed or not new:
        return

    def _get_comp(spec, name):
        return spec.get('components', {}).get(comp_type, {}).get(name)

    candidates = {} # old_name -> {new_name: count/score}

    if use_propagation:
        # Propagation Phase (Schemas specific)
        def _register_candidate(old_ref, new_ref):
            if old_ref and new_ref and isinstance(old_ref, str) and isinstance(new_ref, str):
                prefix = f'#/components/{comp_type}/'
                if old_ref.startswith(prefix) and new_ref.startswith(prefix):
                    old_name = old_ref.split('/')[-1]
                    new_name = new_ref.split('/')[-1]
                    if old_name in removed and new_name in new:
                        candidates.setdefault(old_name, {})[new_name] = candidates[old_name].get(new_name, 0) + 1

        # Seed from endpoints/other modified components
        def _scan_refs(data, visited=None):
            if visited is None: visited = set()
            if id(data) in visited: return
            visited.add(id(data))
            if isinstance(data, dict):
                if '$ref' in data and isinstance(data['$ref'], dict) and 'old' in data['$ref'] and 'new' in data['$ref']:
                    _register_candidate(data['$ref']['old'], data['$ref']['new'])
                
                # Check for 1-to-1 replacement in added/removed lists (e.g. allOf/oneOf changes)
                if 'added' in data and 'removed' in data:
                    added = data['added']
                    removed_items = data['removed']
                    if isinstance(added, list) and isinstance(removed_items, list):
                        if len(added) == 1 and len(removed_items) == 1:
                            old_item = removed_items[0]
                            new_item = added[0]
                            
                            if isinstance(old_item, dict) and '$ref' in old_item and \
                               isinstance(new_item, dict) and '$ref' in new_item:
                                _register_candidate(old_item['$ref'], new_item['$ref'])

                for v in data.values(): _scan_refs(v, visited)
            elif isinstance(data, list):
                for i in data: _scan_refs(i, visited)
        
        _scan_refs(result.modified_paths)
        _scan_refs(result.modified_components)
    else:
        # Content-Based Candidate Generation (Greedy matching for non-propagating types)
        for o_name in removed:
            old_def = _get_comp(old_spec, o_name)
            for n_name in new:
                new_def = _get_comp(new_spec, n_name)
                if old_def and new_def and content_matcher(old_def, new_def):
                    candidates.setdefault(o_name, {})[n_name] = 100 # High score for identical

    # Resolution Logic (Shared)
    final_renames = {}
    
    # 1. Identical Content Priority
    # Iterate over a sorted list to ensure deterministic behavior
    for o_name in sorted(list(removed)):
        old_def = _get_comp(old_spec, o_name)
        if not old_def: continue # Should not happen if it was in removed_components
        
        identical_targets = []
        for n_name in sorted(list(new)):
            new_def = _get_comp(new_spec, n_name)
            if new_def and content_matcher(old_def, new_def):
                identical_targets.append(n_name)
        
        if len(identical_targets) == 1:
            final_renames[o_name] = (identical_targets[0], "Rename")
        elif len(identical_targets) > 1:
            # Ambiguous - use candidates (votes) or lexicographical
            best_match = None
            max_votes = -1
            for t in identical_targets:
                votes = candidates.get(o_name, {}).get(t, 0)
                if votes > max_votes: max_votes, best_match = votes, t
                elif votes == max_votes:
                    if best_match is None or t < best_match: best_match = t
            if best_match: final_renames[o_name] = (best_match, "Rename")

    # Update processed sets for the next step
    # Create copies to modify
    current_removed = list(removed)
    current_new = list(new)

    for o, (n, s) in final_renames.items():
        if o in current_removed: current_removed.remove(o)
        if n in current_new: current_new.remove(n)

    # 2. Similarity Match (Remaining unmatched items)
    # For non-propagating types, if there's a 1-to-1 match left, assume it's a modification
    if not use_propagation:
        if len(current_removed) == 1 and len(current_new) == 1:
            o_name = current_removed[0]
            n_name = current_new[0]
            final_renames[o_name] = (n_name, "Modification")
            current_removed.clear()
            current_new.clear()
    else: # For schemas, use the iterative propagation logic to find more candidates
        # This part of the logic was in the original _detect_renamed_schemas
        # It's about finding more candidates through structural comparison, not resolving.
        # The current structure resolves candidates based on content_matcher and votes.
        # If we want to re-introduce structural propagation for schemas, it needs to be
        # integrated into the candidate generation phase or as a separate pass.
        # For now, the _scan_refs seeds initial candidates, and the resolution logic handles them.
        pass

    # Finalize Renames and Compute Diffs
    if final_renames:
        result.renamed_components.setdefault(comp_type, {}).update({k: v[0] for k, v in final_renames.items()})
        
        # Update the result's new/removed lists based on what was renamed
        # Make sure to operate on the actual lists in result, not copies
        result_new_list = result.new_components.get(comp_type, [])
        result_removed_list = result.removed_components.get(comp_type, [])
        
        for old, (new_name, status) in final_renames.items():
            if old in result_removed_list:
                result_removed_list.remove(old)
            if new_name in result_new_list:
                result_new_list.remove(new_name)
            
            old_def = _get_comp(old_spec, old)
            new_def = _get_comp(new_spec, new_name)
            diff = item_comparator(old_def, new_def)
            
            # Annotate diff with rename info
            diff['__rename_info__'] = {'new_name': new_name, 'status': status}
            result.modified_components.setdefault(comp_type, {})[old] = diff
        
        result.new_components[comp_type] = result_new_list
        result.removed_components[comp_type] = result_removed_list

def _is_deeply_identical(old_s, new_s, visited=None, debug=False):
    old_s = _unwrap_schema(old_s)
    new_s = _unwrap_schema(new_s)
    
    if visited is None: visited = set()
    
    pair_id = (id(old_s), id(new_s))
    if pair_id in visited:
        return True
    visited.add(pair_id)

    # 1. Compare Constraints
    constraints = ['type', 'format', 'minLength', 'maxLength', 'pattern', 'enum', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'minItems', 'maxItems', 'uniqueItems', 'minProperties', 'maxProperties', 'required', 'nullable', 'readOnly', 'writeOnly', 'deprecated']
    for c in constraints:
        if not _is_effectively_equal(old_s.get(c), new_s.get(c)):
            if debug: print(f"    Diff in constraint '{c}': {old_s.get(c)} != {new_s.get(c)}")
            return False

    # 2. Compare Properties
    old_props = old_s.get('properties', {})
    new_props = new_s.get('properties', {})
    if set(old_props.keys()) != set(new_props.keys()):
        if debug: print(f"    Diff in properties keys: {set(old_props.keys())} != {set(new_props.keys())}")
        return False
    for k in old_props:
        if not _is_deeply_identical(old_props[k], new_props[k], visited, debug):
            if debug: print(f"    Diff in property '{k}'")
            return False

    # 3. Compare Items
    if 'items' in old_s or 'items' in new_s:
        if 'items' not in old_s or 'items' not in new_s:
            if debug: print("    Diff in items existence")
            return False
        if not _is_deeply_identical(old_s['items'], new_s['items'], visited, debug):
            if debug: print("    Diff in items content")
            return False

    # 4. Compare Combinators
    for k in ['allOf', 'anyOf', 'oneOf']:
        if k in old_s or k in new_s:
            if k not in old_s or k not in new_s:
                if debug: print(f"    Diff in combinator '{k}' existence")
                return False
            ol = old_s[k]
            nl = new_s[k]
            if len(ol) != len(nl):
                if debug: print(f"    Diff in combinator '{k}' length")
                return False
            for i in range(len(ol)):
                if not _is_deeply_identical(ol[i], nl[i], visited, debug):
                    if debug: print(f"    Diff in combinator '{k}' item {i}")
                    return False

    # 5. Compare $ref
    old_ref = old_s.get('$ref')
    new_ref = new_s.get('$ref')
    
    if old_ref and new_ref:
        if old_ref == new_ref:
            return True
        
        # This part needs to be generalized to _get_comp for the specific comp_type
        # For schemas, it would be:
        if old_ref.startswith('#/components/schemas/'):
            old_target_name = old_ref.split('/')[-1]
            old_target = old_spec.get('components', {}).get('schemas', {}).get(old_target_name)
        else:
            old_target = None
            
        if new_ref.startswith('#/components/schemas/'):
            new_target_name = new_ref.split('/')[-1]
            new_target = new_spec.get('components', {}).get('schemas', {}).get(new_target_name)
        else:
            new_target = None

        if old_target and new_target:
            if debug: print(f"    Recursing into ref: {old_ref} -> {new_ref}")
            return _is_deeply_identical(old_target, new_target, visited, debug)
        else:
            if debug: print(f"    Ref resolution failed: {old_ref} vs {new_ref}")
            return old_ref == new_ref
    elif old_ref or new_ref:
        if debug: print(f"    Diff in ref existence: {old_ref} vs {new_ref}")
        return False

    return True

def _compare_header(old_h, new_h):
    # Headers are similar to parameters (minus 'in' and 'name')
    diff = {}
    for key in ['description', 'required', 'deprecated', 'style', 'explode', 'schema']:
        if key == 'schema':
             if 'schema' in old_h or 'schema' in new_h:
                s_diff = _compare_schema(old_h.get('schema', {}), new_h.get('schema', {}))
                if s_diff: diff['schema'] = s_diff
        elif not _is_effectively_equal(old_h.get(key), new_h.get(key)):
            diff[key] = {'old': old_h.get(key), 'new': new_h.get(key)}

    # Custom Extensions
    ext_diff = _compare_extensions(old_h, new_h)
    if ext_diff: diff.update(ext_diff)

    return diff

def _compare_link(old_l, new_l):
    diff = {}
    for key in ['operationRef', 'operationId', 'description', 'server']:
        if not _is_effectively_equal(old_l.get(key), new_l.get(key)):
            diff[key] = {'old': old_l.get(key), 'new': new_l.get(key)}
    return diff

def _compare_callback(old_c, new_c):
    # Callbacks are maps of Path Items
    # For simplicity, just check equality or basic diff
    # A full recursive path comparison would be needed for deep diff
    if not _is_effectively_equal(old_c, new_c): # Changed from old_c != new_c
        return {'old': 'modified', 'new': 'modified'} # Placeholder for deep diff
    return {}

def _compare_example(old_e: Dict, new_e: Dict) -> Dict:
    diff = {}
    for key in ['summary', 'description', 'value', 'externalValue']:
        if not _is_effectively_equal(old_e.get(key), new_e.get(key)):
            diff[key] = {'old': old_e.get(key), 'new': new_e.get(key)}
    
    # Custom Extensions
    ext_diff = _compare_extensions(old_e, new_e)
    if ext_diff: diff.update(ext_diff)
    
    return diff

def _compare_security_scheme(old_s, new_s):
    diff = {}
    for key in ['type', 'description', 'name', 'in', 'scheme', 'bearerFormat', 'flows', 'openIdConnectUrl']:
        if not _is_effectively_equal(old_s.get(key), new_s.get(key)):
            diff[key] = {'old': old_s.get(key), 'new': new_s.get(key)}
    return diff

def _unwrap_schema(schema: Any) -> Any:
    """
    Normalizes schemas by unwrapping single-item allOf/anyOf/oneOf wrappers.
    e.g., {"allOf": [{"$ref": "..."}]} -> {"$ref": "..."}
    """
    if not isinstance(schema, dict):
        return schema
        
    comb_keys = ['allOf', 'anyOf', 'oneOf']
    for k in comb_keys:
        if k in schema and len(schema) == 1:
            val = schema[k]
            if isinstance(val, list) and len(val) == 1:
                return _unwrap_schema(val[0])
    return schema

def _compare_schema(old_schema: Dict, new_schema: Dict) -> Dict:
    old_schema = _unwrap_schema(old_schema)
    new_schema = _unwrap_schema(new_schema)
    
    diff = {}
    # Check constraints
    constraints = ['type', 'format', 'description', 'minLength', 'maxLength', 'pattern', 'enum', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'minItems', 'maxItems', 'uniqueItems', 'minProperties', 'maxProperties', 'required', 'nullable', 'readOnly', 'writeOnly', 'deprecated']
    
    for c in constraints:
        # Handle list comparison for enum and required by converting to set if order doesn't matter? 
        # For now, strict equality
        if not _is_effectively_equal(old_schema.get(c), new_schema.get(c)):
             diff[c] = {'old': old_schema.get(c), 'new': new_schema.get(c)}

    # Custom Extensions
    ext_diff = _compare_extensions(old_schema, new_schema)
    if ext_diff: diff.update(ext_diff)
             
    # Check $ref
    if not _is_effectively_equal(old_schema.get('$ref'), new_schema.get('$ref')): # Changed from old_schema.get('$ref') != new_schema.get('$ref')
        diff['$ref'] = {'old': old_schema.get('$ref'), 'new': new_schema.get('$ref')}
        
    # Check properties recursively
    if 'properties' in old_schema or 'properties' in new_schema:
        props_diff = _compare_properties(old_schema.get('properties', {}), new_schema.get('properties', {}))
        if props_diff:
            diff['properties'] = props_diff
            
    # Check items (for arrays)
    if 'items' in old_schema or 'items' in new_schema:
        items_diff = _compare_schema(old_schema.get('items', {}), new_schema.get('items', {}))
        if items_diff:
            diff['items'] = items_diff

    # Check allOf, anyOf, oneOf
    for combinator in ['allOf', 'anyOf', 'oneOf']:
        if combinator in old_schema or combinator in new_schema:
            old_comb = old_schema.get(combinator, [])
            new_comb = new_schema.get(combinator, [])
            
            added = []
            removed = []
            
            # Find added items
            for new_item in new_comb:
                is_new = True
                for old_item in old_comb:
                    # If compare returns empty dict, they are effectively equal
                    if not _compare_schema(old_item, new_item):
                        is_new = False
                        break
                if is_new:
                    added.append(new_item)
            
            # Find removed items
            for old_item in old_comb:
                is_removed = True
                for new_item in new_comb:
                    if not _compare_schema(old_item, new_item):
                        is_removed = False
                        break
                if is_removed:
                    removed.append(old_item)
            
            if added or removed:
                diff[combinator] = {'added': added, 'removed': removed}
            
            # If no adds/removes but lengths match, check for modifications in place?
            # The set logic above handles modifications as "remove old + add new" which is technically correct for a list of options.
            # So we don't need the index-based comparison anymore.

    return diff

def _compare_properties(old_props: Dict, new_props: Dict) -> Dict:
    diff = {}
    old_keys = set(old_props.keys())
    new_keys = set(new_props.keys())
    
    diff['new'] = list(new_keys - old_keys)
    diff['removed'] = list(old_keys - new_keys)
    
    for prop in old_keys & new_keys:
        prop_diff = _compare_schema(old_props[prop], new_props[prop])
        if prop_diff:
            diff.setdefault('modified', {})[prop] = prop_diff
            
    if not diff['new'] and not diff['removed'] and 'modified' not in diff:
        return {}
        
    return diff
