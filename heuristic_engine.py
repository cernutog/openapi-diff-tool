from typing import List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class Insight:
    rule_id: str
    title: str
    description: str
    severity: Severity
    category: str # ENDPOINT, PARAMETER, SCHEMA, SECURITY, etc.
    context: Optional[str] = None # e.g., "GET /users"

class HeuristicEngine:
    def __init__(self, diff: Any):
        # diff is a DiffResult object
        self.diff = diff
        self.insights: List[Insight] = []

    def run(self) -> List[Insight]:
        self.insights = []
        self._analyze_endpoints()
        self._analyze_parameters()
        self._analyze_schemas()
        self._analyze_request_bodies()
        return self.insights

    def _analyze_endpoints(self):
        """
        Implements Endpoint Rules (E01-E10)
        """
        # E01: Operation Removed
        if hasattr(self.diff, 'removed_paths'):
            for path in self.diff.removed_paths:
                self.insights.append(Insight(
                    rule_id="E01",
                    title="Endpoint Removed",
                    description=f"The resource '{path}' has been completely removed. Clients using this endpoint will receive 404 errors.",
                    severity=Severity.CRITICAL,
                    category="ENDPOINT",
                    context=path
                ))
        
        if hasattr(self.diff, 'modified_paths'):
            for path, p_changes in self.diff.modified_paths.items():
                # E01 (Partial): Specific Method Removed
                if 'removed_ops' in p_changes:
                    for method in p_changes['removed_ops']:
                        self.insights.append(Insight(
                            rule_id="E01",
                            title="Operation Removed",
                            description=f"The HTTP method '{method.upper()}' for '{path}' has been removed.",
                            severity=Severity.CRITICAL,
                            category="ENDPOINT",
                            context=f"{method.upper()} {path}"
                        ))

                if 'modified_ops' in p_changes:
                    for method, op_changes in p_changes['modified_ops'].items():
                        method_upper = method.upper()
                        context = f"{method_upper} {path}"
                        
                        # E04: Deprecation Added
                        if 'deprecated' in op_changes:
                            dep = op_changes['deprecated']
                            if dep.get('new') is True and dep.get('old') is not True:
                                self.insights.append(Insight(
                                    rule_id="E04",
                                    title="Endpoint Deprecated",
                                    description=f"The endpoint '{context}' has been marked as deprecated. Plan for migration.",
                                    severity=Severity.MEDIUM,
                                    category="ENDPOINT",
                                    context=context
                                ))
                            # E05: Deprecation Removed
                            elif dep.get('new') is False and dep.get('old') is True:
                                self.insights.append(Insight(
                                    rule_id="E05",
                                    title="Deprecation Revoked",
                                    description=f"The endpoint '{context}' is no longer deprecated.",
                                    severity=Severity.LOW,
                                    category="ENDPOINT",
                                    context=context
                                ))

                        # E03: Operation ID Changed
                        if 'operationId' in op_changes:
                            self.insights.append(Insight(
                                rule_id="E03",
                                title="Operation ID Changed",
                                description=f"The operationId changed from '{op_changes['operationId']['old']}' to '{op_changes['operationId']['new']}'. Generated SDKs will break.",
                                severity=Severity.HIGH,
                                category="ENDPOINT",
                                context=context
                            ))
                        
                        # E07: Summary/Description Changed
                        if 'summary' in op_changes or 'description' in op_changes:
                            self.insights.append(Insight(
                                rule_id="E07",
                                title="Documentation Updated",
                                description="Summary or description has been updated.",
                                severity=Severity.INFO,
                                category="ENDPOINT",
                                context=context
                            ))

                        # E06: Tags Modified
                        if 'tags' in op_changes:
                            self.insights.append(Insight(
                                rule_id="E06",
                                title="Tags Modified",
                                description="Endpoint tags have been reorganized.",
                                severity=Severity.LOW,
                                category="ENDPOINT",
                                context=context
                            ))

    def _analyze_parameters(self):
        """
        Implements Parameter Rules (P01-P12)
        """
        if not hasattr(self.diff, 'modified_paths'):
            return

        for path, p_changes in self.diff.modified_paths.items():
            if 'modified_ops' not in p_changes:
                continue
                
            for method, op_changes in p_changes['modified_ops'].items():
                if 'parameters' not in op_changes:
                    continue
                
                params = op_changes['parameters']
                context = f"{method.upper()} {path}"

                # P01: Parameter Removed
                if 'removed' in params:
                    for p_name in params['removed']:
                        self.insights.append(Insight(
                            rule_id="P01",
                            title="Parameter Removed",
                            description=f"Parameter '{p_name}' has been removed. Clients sending it may receive errors.",
                            severity=Severity.CRITICAL,
                            category="PARAMETER",
                            context=context
                        ))

                # P02: Required Param Added
                if 'added_required' in params:
                    for p_name in params['added_required']:
                        self.insights.append(Insight(
                            rule_id="P02",
                            title="New Required Parameter",
                            description=f"New required parameter '{p_name}' added. Existing clients will fail.",
                            severity=Severity.CRITICAL,
                            category="PARAMETER",
                            context=context
                        ))

                # P03: Optional Param Added
                if 'added_optional' in params:
                    for p_name in params['added_optional']:
                        self.insights.append(Insight(
                            rule_id="P03",
                            title="New Optional Parameter",
                            description=f"New optional parameter '{p_name}' available.",
                            severity=Severity.LOW,
                            category="PARAMETER",
                            context=context
                        ))

                # Modified Parameters
                if 'modified' in params:
                    for p_name, p_diff in params['modified'].items():
                        p_context = f"{context} (param: {p_name})"
                        
                        # P04/P05: Required Flag Changed
                        if 'required' in p_diff:
                            req = p_diff['required']
                            if req['new'] is True:
                                self.insights.append(Insight(
                                    rule_id="P04",
                                    title="Parameter Made Required",
                                    description=f"Parameter '{p_name}' is now required.",
                                    severity=Severity.CRITICAL,
                                    category="PARAMETER",
                                    context=p_context
                                ))
                            else:
                                self.insights.append(Insight(
                                    rule_id="P05",
                                    title="Parameter Made Optional",
                                    description=f"Parameter '{p_name}' is no longer required.",
                                    severity=Severity.LOW, # RELAXED
                                    category="PARAMETER",
                                    context=p_context
                                ))

                        # P06: Location Changed
                        if 'in' in p_diff:
                            self.insights.append(Insight(
                                rule_id="P06",
                                title="Parameter Location Changed",
                                description=f"Parameter '{p_name}' moved from {p_diff['in']['old']} to {p_diff['in']['new']}.",
                                severity=Severity.CRITICAL,
                                category="PARAMETER",
                                context=p_context
                            ))

                        # Schema Changes
                        if 'schema' in p_diff:
                            s_diff = p_diff['schema']
                            
                            # P07: Type Changed
                            if 'type' in s_diff:
                                self.insights.append(Insight(
                                    rule_id="P07",
                                    title="Parameter Type Changed",
                                    description=f"Type changed from {s_diff['type']['old']} to {s_diff['type']['new']}.",
                                    severity=Severity.CRITICAL,
                                    category="PARAMETER",
                                    context=p_context
                                ))
                            
                            # P10: Enum Removed
                            if 'enum' in s_diff and 'removed' in s_diff['enum']:
                                self.insights.append(Insight(
                                    rule_id="P10",
                                    title="Enum Values Removed",
                                    description=f"Valid values removed: {s_diff['enum']['removed']}.",
                                    severity=Severity.CRITICAL,
                                    category="PARAMETER",
                                    context=p_context
                                ))

    def _analyze_schemas(self):
        """
        Implements Schema Rules (S01-S15)
        """
        if not hasattr(self.diff, 'modified_components') or 'schemas' not in self.diff.modified_components:
            return

        for s_name, s_changes in self.diff.modified_components['schemas'].items():
            context = f"Schema: {s_name}"

            # S02: Required Property Added
            if 'required' in s_changes:
                new_val = s_changes['required'].get('new')
                old_val = s_changes['required'].get('old')
                new_req = set(new_val if new_val is not None else [])
                old_req = set(old_val if old_val is not None else [])
                added = new_req - old_req
                if added:
                    self.insights.append(Insight(
                        rule_id="S02",
                        title="New Required Property",
                        description=f"Properties made required: {', '.join(added)}.",
                        severity=Severity.CRITICAL,
                        category="SCHEMA",
                        context=context
                    ))

            # Properties
            if 'properties' in s_changes:
                props = s_changes['properties']
                
                # S01: Property Removed
                if 'removed' in props:
                    self.insights.append(Insight(
                        rule_id="S01",
                        title="Property Removed",
                        description=f"Properties removed: {', '.join(props['removed'])}.",
                        severity=Severity.CRITICAL,
                        category="SCHEMA",
                        context=context
                    ))

                # Modified Properties
                if 'modified' in props:
                    for prop, p_diff in props['modified'].items():
                        p_context = f"{context}.{prop}"
                        
                        # S03: Type Changed
                        if 'type' in p_diff:
                            self.insights.append(Insight(
                                rule_id="S03",
                                title="Property Type Changed",
                                description=f"Type changed from {p_diff['type']['old']} to {p_diff['type']['new']}.",
                                severity=Severity.CRITICAL,
                                category="SCHEMA",
                                context=p_context
                            ))
                        
                        # S08: Pattern Changed
                        if 'pattern' in p_diff:
                            self.insights.append(Insight(
                                rule_id="S08",
                                title="Regex Pattern Changed",
                                description="Validation pattern has been modified.",
                                severity=Severity.HIGH,
                                category="SCHEMA",
                                context=p_context
                            ))

            # S12: OneOf/AnyOf Changes
            for comb in ['oneOf', 'anyOf', 'allOf']:
                if comb in s_changes:
                    self.insights.append(Insight(
                        rule_id="S12",
                        title=f"{comb} Modified",
                        description=f"Polymorphic options for {comb} have changed.",
                        severity=Severity.HIGH,
                        category="SCHEMA",
                        context=context
                    ))

    def _analyze_request_bodies(self):
        """
        Implements Request Body Rules (B01-B08)
        """
        if not hasattr(self.diff, 'modified_paths'):
            return

        for path, p_changes in self.diff.modified_paths.items():
            if 'modified_ops' not in p_changes:
                continue
                
            for method, op_changes in p_changes['modified_ops'].items():
                if 'requestBody' not in op_changes:
                    continue
                
                rb = op_changes['requestBody']
                context = f"{method.upper()} {path} (Body)"

                # B05: Body Made Required
                if 'required' in rb:
                    if rb['required']['new'] is True:
                        self.insights.append(Insight(
                            rule_id="B05",
                            title="Request Body Required",
                            description="Request body is now mandatory.",
                            severity=Severity.CRITICAL,
                            category="REQUEST_BODY",
                            context=context
                        ))

                # B03: Content-Type Removed
                if 'content' in rb and 'removed' in rb['content']:
                    self.insights.append(Insight(
                        rule_id="B03",
                        title="Content-Type Removed",
                        description=f"Media types removed: {', '.join(rb['content']['removed'])}.",
                        severity=Severity.CRITICAL,
                        category="REQUEST_BODY",
                        context=context
                    ))
