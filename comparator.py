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

    # Detect Renamed Schemas (Iterative Propagation)
    _detect_renamed_schemas(result, old_spec, new_spec)

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

def _compare_info(old_info: Dict, new_info: Dict, result: DiffResult):
    for key in ['title', 'version', 'description', 'termsOfService', 'contact', 'license']:
        old_val = old_info.get(key)
        new_val = new_info.get(key)
        if old_val != new_val:
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
        if old_op.get(key) != new_op.get(key):
            diff[key] = {'old': old_op.get(key), 'new': new_op.get(key)}

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
        if old_param.get(key) != new_param.get(key):
            diff[key] = {'old': old_param.get(key), 'new': new_param.get(key)}
            
    # Check schema
    if 'schema' in old_param or 'schema' in new_param:
        schema_diff = _compare_schema(old_param.get('schema', {}), new_param.get('schema', {}))
        if schema_diff:
            diff['schema'] = schema_diff
            
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
        
    return diff

def _compare_response(old_resp: Dict, new_resp: Dict) -> Dict:
    diff = {}
    if old_resp.get('description') != new_resp.get('description'):
        diff['description'] = {'old': old_resp.get('description'), 'new': new_resp.get('description')}
        
    # Compare Content
    old_content = old_resp.get('content', {})
    new_content = new_resp.get('content', {})
    content_diff = _compare_dict_items(old_content, new_content, _compare_media_type)
    if content_diff:
        diff['content'] = content_diff
        
    return diff

def _compare_media_type(old_mt: Dict, new_mt: Dict) -> Dict:
    diff = {}
    if 'schema' in old_mt or 'schema' in new_mt:
        schema_diff = _compare_schema(old_mt.get('schema', {}), new_mt.get('schema', {}))
        if schema_diff:
            diff['schema'] = schema_diff
    return diff

def _compare_dict_items(old_dict: Dict, new_dict: Dict, item_comparator) -> Dict:
    diff = {}
    old_keys = set(old_dict.keys())
    new_keys = set(new_dict.keys())
    
    diff['new'] = list(new_keys - old_keys)
    diff['removed'] = list(old_keys - new_keys)
    
    for key in old_keys & new_keys:
        item_diff = item_comparator(old_dict[key], new_dict[key])
        if item_diff:
            diff.setdefault('modified', {})[key] = item_diff
            
    if not diff['new'] and not diff['removed'] and 'modified' not in diff:
        return {}
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

def _detect_renamed_schemas(result: DiffResult, old_spec: Dict, new_spec: Dict):
    """
    Iterative Rename Propagation with Deterministic Resolution.
    1. Find 'Seed' renames from Endpoints (Roots).
    2. Propagate renames based on structure.
    3. Resolve candidates:
       - Exact Content Match -> Rename (Priority)
       - Single Candidate (Different Content) -> Modification
       - Multiple Candidates (Different Content) -> Ambiguous (Unmatched)
    4. Compute and store diffs for all resolved pairs.
    """
    removed_schemas = set(result.removed_components.get('schemas', []))
    new_schemas = set(result.new_components.get('schemas', []))
    
    if not removed_schemas or not new_schemas:
        return

    # Map old_name -> dict of {new_name: count}
    candidates = {} 

    def _register_candidate(old_ref, new_ref):
        if old_ref and new_ref and isinstance(old_ref, str) and isinstance(new_ref, str):
            if old_ref.startswith('#/components/schemas/') and new_ref.startswith('#/components/schemas/'):
                old_name = old_ref.split('/')[-1]
                new_name = new_ref.split('/')[-1]
                
                if old_name in removed_schemas and new_name in new_schemas:
                    if old_name not in candidates:
                        candidates[old_name] = {}
                    candidates[old_name][new_name] = candidates[old_name].get(new_name, 0) + 1

    def _check_ref_change(change_val):
        if isinstance(change_val, dict) and '$ref' in change_val:
            ref_change = change_val['$ref']
            if isinstance(ref_change, dict) and 'old' in ref_change and 'new' in ref_change:
                _register_candidate(ref_change['old'], ref_change['new'])

    # 1. Seed Phase: Scan Endpoints (Paths) for initial renames
    def _scan_paths(data, visited=None):
        if visited is None: visited = set()
        if id(data) in visited: return
        visited.add(id(data))

        if isinstance(data, dict):
            if '$ref' in data and 'old' in data['$ref'] and 'new' in data['$ref']:
                 _check_ref_change(data)
            
            # Check for 1-to-1 replacement in added/removed lists (e.g. allOf/oneOf changes)
            if 'added' in data and 'removed' in data:
                added = data['added']
                removed = data['removed']
                if isinstance(added, list) and isinstance(removed, list):
                    if len(added) == 1 and len(removed) == 1:
                        old_item = removed[0]
                        new_item = added[0]
                        
                        if isinstance(old_item, dict) and '$ref' in old_item and \
                           isinstance(new_item, dict) and '$ref' in new_item:
                            _register_candidate(old_item['$ref'], new_item['$ref'])

            for key, value in data.items():
                _scan_paths(value, visited)
        elif isinstance(data, list):
            for item in data:
                _scan_paths(item, visited)
    
    _scan_paths(result.modified_paths)
    _scan_paths(result.modified_components) 

    # 2. Propagation Phase
    def _get_schema(spec, name):
        return spec.get('components', {}).get('schemas', {}).get(name)

    def _compare_and_propagate(old_s, new_s):
        # Compare properties
        old_props = old_s.get('properties', {})
        new_props = new_s.get('properties', {})
        
        for prop in old_props:
            if prop in new_props:
                op = old_props[prop]
                np = new_props[prop]
                
                # Direct Ref
                if '$ref' in op and '$ref' in np:
                    _register_candidate(op['$ref'], np['$ref'])
                
                # Array Items Ref
                if 'items' in op and 'items' in np:
                    if '$ref' in op['items'] and '$ref' in np['items']:
                        _register_candidate(op['items']['$ref'], np['items']['$ref'])

        # allOf/anyOf/oneOf
        for k in ['allOf', 'anyOf', 'oneOf']:
            if k in old_s and k in new_s:
                ol = old_s[k]
                nl = new_s[k]
                
                if len(ol) == len(nl):
                    for i in range(len(ol)):
                        if '$ref' in ol[i] and '$ref' in nl[i]:
                            _register_candidate(ol[i]['$ref'], nl[i]['$ref'])

    def _is_deeply_identical(old_s, new_s, visited=None, debug=False):
        if visited is None: visited = set()
        
        pair_id = (id(old_s), id(new_s))
        if pair_id in visited:
            return True
        visited.add(pair_id)

        # 1. Compare Constraints
        constraints = ['type', 'format', 'minLength', 'maxLength', 'pattern', 'enum', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'minItems', 'maxItems', 'uniqueItems', 'minProperties', 'maxProperties', 'required', 'nullable', 'readOnly', 'writeOnly', 'deprecated']
        for c in constraints:
            if old_s.get(c) != new_s.get(c):
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
            
            if old_ref.startswith('#/components/schemas/'):
                old_target_name = old_ref.split('/')[-1]
                old_target = _get_schema(old_spec, old_target_name)
            else:
                old_target = None
                
            if new_ref.startswith('#/components/schemas/'):
                new_target_name = new_ref.split('/')[-1]
                new_target = _get_schema(new_spec, new_target_name)
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

    def _is_content_identical(old_s, new_s, debug=False):
        return _is_deeply_identical(old_s, new_s, debug=debug)

    def _count_diff_size(diff):
        """Recursively count the number of leaf changes in a diff dict."""
        if not isinstance(diff, dict): return 1
        count = 0
        for k, v in diff.items():
            if k in ['old', 'new'] and not isinstance(v, dict): # Leaf change
                count += 1
            elif isinstance(v, dict):
                count += _count_diff_size(v)
            elif isinstance(v, list): # Added/Removed lists
                count += len(v)
        return count

    # Iteration Loop
    processed_pairs = set()
    
    while True:
        # Determine current valid renames (Resolution Logic)
        current_renames = {} # old_name -> (new_name, status)
        
        for old_name, targets_dict in candidates.items():
            old_def = _get_schema(old_spec, old_name)
            if not old_def: continue

            # 1. Filter for identical content
            identical_targets = []
            for t in targets_dict.keys():
                new_def = _get_schema(new_spec, t)
                is_id = new_def and _is_content_identical(old_def, new_def)
                if is_id:
                    identical_targets.append(t)
            
            if len(identical_targets) == 1:
                # Case A: Exactly One Identical Candidate -> RENAME (Priority)
                winner = identical_targets[0]
                current_renames[old_name] = (winner, "Rename")
            elif len(identical_targets) > 1:
                # Case C: Multiple Identical Candidates -> Ambiguous
                # Resolve by Voting (Usage Count)
                best_match = None
                max_votes = -1
                
                for t in identical_targets:
                    votes = targets_dict.get(t, 0)
                    if votes > max_votes:
                        max_votes = votes
                        best_match = t
                    elif votes == max_votes:
                        # Tie-breaker: Lexicographical for determinism (no name similarity logic)
                        if best_match is None or t < best_match:
                            best_match = t
                
                if best_match:
                    current_renames[old_name] = (best_match, "Rename")
            else:
                # Case B: No Identical Candidates -> Try Least Differences
                best_target = None
                min_score = float('inf')
                
                # Sort targets for deterministic tie-breaking (lexicographical)
                sorted_targets = sorted(list(targets_dict.keys()))
                
                for t in sorted_targets:
                    new_def = _get_schema(new_spec, t)
                    if not new_def: continue
                    
                    diff = _compare_schema(old_def, new_def)
                    score = _count_diff_size(diff)
                    
                    if score < min_score:
                        min_score = score
                        best_target = t
                
                if best_target:
                    current_renames[old_name] = (best_target, "Modification")
        
        # Check if we found anything new to process
        new_work = False
        for old_name, (new_name, status) in current_renames.items():
            pair = (old_name, new_name)
            if pair not in processed_pairs:
                processed_pairs.add(pair)
                
                # Look up definitions
                old_def = _get_schema(old_spec, old_name)
                new_def = _get_schema(new_spec, new_name)
                
                if old_def and new_def:
                    _compare_and_propagate(old_def, new_def)
                    new_work = True
        
        if not new_work:
            break

    # Finalize Renames and Compute Diffs
    final_renames = {}
    for old_name, targets_dict in candidates.items():
        # Re-apply resolution logic one last time to get final set
        old_def = _get_schema(old_spec, old_name)
        if not old_def: continue

        identical_targets = []
        for t in targets_dict.keys():
            new_def = _get_schema(new_spec, t)
            if new_def and _is_content_identical(old_def, new_def):
                identical_targets.append(t)
        
        if len(identical_targets) == 1:
            final_renames[old_name] = (identical_targets[0], "Rename")
        elif len(identical_targets) > 1:
            # Ambiguous identicals - try voting
            best_match = None
            max_votes = -1
            
            for t in identical_targets:
                votes = targets_dict.get(t, 0)
                if votes > max_votes:
                    max_votes = votes
                    best_match = t
                elif votes == max_votes:
                    # Tie-breaker: Lexicographical
                    if best_match is None or t < best_match:
                        best_match = t
            
            if best_match:
                final_renames[old_name] = (best_match, "Rename")
        else:
            # No identicals
            if len(targets_dict) == 1:
                final_renames[old_name] = (list(targets_dict.keys())[0], "Modification")
            else:
                # Multiple different candidates -> Try Least Differences
                best_target = None
                min_score = float('inf')
                sorted_targets = sorted(list(targets_dict.keys()))
                
                for t in sorted_targets:
                    new_def = _get_schema(new_spec, t)
                    if not new_def: continue
                    diff = _compare_schema(old_def, new_def)
                    score = _count_diff_size(diff)
                    if score < min_score:
                        min_score = score
                        best_target = t
                
                if best_target:
                    final_renames[old_name] = (best_target, "Modification")

    if final_renames:
        # Store simple mapping for backward compatibility if needed, 
        # but primarily we want to store the diffs.
        result.renamed_components['schemas'] = {k: v[0] for k, v in final_renames.items()}
        
        # Remove from New/Removed lists
        current_new = result.new_components.get('schemas', [])
        current_removed = result.removed_components.get('schemas', [])
        
        for old, (new, status) in final_renames.items():
            if old in current_removed:
                current_removed.remove(old)
            if new in current_new:
                current_new.remove(new)
            
            # COMPUTE AND STORE DIFF
            old_def = _get_schema(old_spec, old)
            new_def = _get_schema(new_spec, new)
            diff = _compare_schema(old_def, new_def)
            
            # Annotate diff with rename info
            diff['__rename_info__'] = {'new_name': new, 'status': status}
            result.modified_components.setdefault('schemas', {})[old] = diff
        
        result.new_components['schemas'] = current_new
        result.removed_components['schemas'] = current_removed

def _compare_header(old_h, new_h):
    # Headers are similar to parameters (minus 'in' and 'name')
    diff = {}
    for key in ['description', 'required', 'deprecated', 'style', 'explode', 'schema']:
        if key == 'schema':
             if 'schema' in old_h or 'schema' in new_h:
                s_diff = _compare_schema(old_h.get('schema', {}), new_h.get('schema', {}))
                if s_diff: diff['schema'] = s_diff
        elif old_h.get(key) != new_h.get(key):
            diff[key] = {'old': old_h.get(key), 'new': new_h.get(key)}
    return diff

def _compare_link(old_l, new_l):
    diff = {}
    for key in ['operationRef', 'operationId', 'description', 'server']:
        if old_l.get(key) != new_l.get(key):
            diff[key] = {'old': old_l.get(key), 'new': new_l.get(key)}
    return diff

def _compare_callback(old_c, new_c):
    # Callbacks are maps of Path Items
    # For simplicity, just check equality or basic diff
    # A full recursive path comparison would be needed for deep diff
    if old_c != new_c:
        return {'old': 'modified', 'new': 'modified'} # Placeholder for deep diff
    return {}

def _compare_example(old_e, new_e):
    diff = {}
    for key in ['summary', 'description', 'value', 'externalValue']:
        if old_e.get(key) != new_e.get(key):
            diff[key] = {'old': old_e.get(key), 'new': new_e.get(key)}
    return diff

def _compare_security_scheme(old_s, new_s):
    diff = {}
    for key in ['type', 'description', 'name', 'in', 'scheme', 'bearerFormat', 'flows', 'openIdConnectUrl']:
        if old_s.get(key) != new_s.get(key):
            diff[key] = {'old': old_s.get(key), 'new': new_s.get(key)}
    return diff

def _compare_schema(old_schema: Dict, new_schema: Dict) -> Dict:
    diff = {}
    # Check constraints
    constraints = ['type', 'format', 'minLength', 'maxLength', 'pattern', 'enum', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'minItems', 'maxItems', 'uniqueItems', 'minProperties', 'maxProperties', 'required', 'nullable', 'readOnly', 'writeOnly', 'deprecated']
    
    for c in constraints:
        # Handle list comparison for enum and required by converting to set if order doesn't matter? 
        # For now, strict equality
        if old_schema.get(c) != new_schema.get(c):
             diff[c] = {'old': old_schema.get(c), 'new': new_schema.get(c)}
             
    # Check $ref
    if old_schema.get('$ref') != new_schema.get('$ref'):
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
