from typing import Dict, List, Any, Set, Tuple

class DependencyTracer:
    """
    Builds a reverse index of schema usage in an OpenAPI specification.
    Maps Schema Name -> List of Usage Contexts (Endpoint, Method, Location).
    """
    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        # Mapping: SchemaName -> List[{'method': str, 'path': str, 'context': str}]
        self.usage_map: Dict[str, List[Dict[str, str]]] = {}
        # Cache for visited schemas to prevent infinite recursion
        self._processed_schemas: Set[str] = set()
        
        self._build_index()

    def get_impacted_endpoints(self, schema_name: str) -> List[Dict[str, str]]:
        """
        Returns a list of endpoints impacted by changes to the given schema.
        Includes usages in:
        - Request Body
        - Responses
        - Parameters
        """
        return self.usage_map.get(schema_name, [])

    def _build_index(self):
        paths = self.spec.get('paths', {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method not in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']:
                    continue
                
                context_base = {'method': method.upper(), 'path': path}
                
                # 1. Trace Request Body
                if 'requestBody' in operation:
                    self._trace_content(operation['requestBody'].get('content', {}), 
                                      {**context_base, 'context': 'Request Body'})

                # 2. Trace Responses
                responses = operation.get('responses', {})
                for status_code, response in responses.items():
                    self._trace_content(response.get('content', {}), 
                                      {**context_base, 'context': f'Response {status_code}'})

                # 3. Trace Parameters
                parameters = operation.get('parameters', [])
                # Also include path-level parameters
                parameters.extend(path_item.get('parameters', []))
                
                for param in parameters:
                    if 'schema' in param:
                        self._trace_schema(param['schema'], 
                                         {**context_base, 'context': f"Param '{param.get('name', '?')}'"})

    def _trace_content(self, content: Dict, context: Dict):
        for media_type, media_obj in content.items():
            if 'schema' in media_obj:
                self._trace_schema(media_obj['schema'], context)

    def _trace_schema(self, schema: Dict, context: Dict):
        """
        Recursively traces a schema object and registers usage for any $ref found.
        """
        if not schema: return

        # Direct Reference
        if '$ref' in schema:
            ref_name = schema['$ref'].split('/')[-1]
            self._register_usage(ref_name, context)
            # We don't recurse into the definition here because we assume
            # the definition itself is analyzed separately if we wanted full graph.
            # But for "Impact Analysis", we just want to know "Who points to me?".
            # However, if Schema A points to Schema B, and Schema B changes, 
            # does that impact Endpoint X that uses Schema A? 
            # YES. So we need to propagate dependencies.
            # BUT: The requirement is usually "Where is THIS schema used?".
            # If "Address" changes, we want to know it's used in "Customer".
            # And if "Customer" is used in "POST /users", we want to know that.
            
            # CURRENT STRATEGY: 
            # Just record direct usage. 
            # A full dependency graph (A->B->C) is needed to show transitive impact.
            # Let's start with direct usage, and maybe expandable.
            # ACTUALLY, usually users want to know: "I changed 'Address', show me the Endpoints".
            # If 'Address' is nested in 'Customer', the user usually sees 'Customer' as modified too.
            # IF 'Customer' is NOT modified (only 'Address' is), then 'Customer' effectively IS modified textually?
            # No, 'Customer' definition might just be {$ref: Address}.
            # If Address content changes, Customer definition doesn't change, but effective schema does.
            # So, we DO need transitive lookup.
            
            # To do transitive lookup efficiently:
            # 1. Build Direct Usage Map: Schema -> UsedIn(Endpoint)
            # 2. Build Schema Dependency Graph: Schema A -> depends on -> Schema B
            # 3. When querying for B, find parents (A) and their usages too.
            return

        # Arrays
        if 'items' in schema:
            self._trace_schema(schema['items'], context)

        # Objects (Properties)
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                self._trace_schema(prop_schema, context)
        
        # Combinators
        for k in ['allOf', 'anyOf', 'oneOf']:
            if k in schema:
                for sub_schema in schema[k]:
                    self._trace_schema(sub_schema, context)
                    
        # Additional Properties
        if 'additionalProperties' in schema and isinstance(schema['additionalProperties'], dict):
             self._trace_schema(schema['additionalProperties'], context)

    def _register_usage(self, schema_name: str, context: Dict):
        if schema_name not in self.usage_map:
            self.usage_map[schema_name] = []
        
        # Avoid duplicates
        if context not in self.usage_map[schema_name]:
            self.usage_map[schema_name].append(context)

    def resolve_transitive_impact(self):
        """
        Expands the usage map to include transitive dependencies.
        If Schema A uses Schema B, then usages of Schema A are also usages of Schema B.
        """
        # First, build a map of Schema -> Parent Schemas
        # We need to scan components/schemas for this.
        schema_parents = {} # Child -> List[Parent]
        
        components = self.spec.get('components', {}).get('schemas', {})
        
        def find_refs(schema, parent_name):
            if not schema: return
            if '$ref' in schema:
                child = schema['$ref'].split('/')[-1]
                if child not in schema_parents: schema_parents[child] = []
                if parent_name not in schema_parents[child]:
                    schema_parents[child].append(parent_name)
            
            if 'items' in schema: find_refs(schema['items'], parent_name)
            if 'properties' in schema:
                for p in schema['properties'].values(): find_refs(p, parent_name)
            for k in ['allOf', 'anyOf', 'oneOf']:
                if k in schema:
                    for s in schema[k]: find_refs(s, parent_name)

        for name, definition in components.items():
            find_refs(definition, name)
            
        # Now propagate usages
        # If I am 'Address' (Child), my usages include my direct usages + usages of 'Customer' (Parent)
        # We need to do this until convergence or topological sort.
        # Simple iterative approach.
        
        changed = True
        while changed:
            changed = False
            for child, parents in schema_parents.items():
                child_usages = self.usage_map.get(child, [])
                initial_len = len(child_usages)
                
                for parent in parents:
                    parent_usages = self.usage_map.get(parent, [])
                    for pu in parent_usages:
                        if pu not in child_usages:
                            child_usages.append(pu)
                            changed = True
                            
                self.usage_map[child] = child_usages
