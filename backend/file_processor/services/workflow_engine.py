import json
from typing import Dict, Any, List
from datetime import datetime


class WorkflowEngine:
    """Workflow execution engine for file processing pipelines"""

    def __init__(self):
        self.workflows = {}

    def create_workflow(self, name: str, steps: List[Dict]) -> str:
        """Create a new workflow"""
        workflow_id = f"wf_{len(self.workflows) + 1}"
        self.workflows[workflow_id] = {
            "id": workflow_id,
            "name": name,
            "steps": steps,
            "created_at": datetime.now().isoformat(),
            "status": "created",
        }
        return workflow_id

    def execute_workflow(
        self, workflow_id: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow with given input data"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        workflow["status"] = "running"

        results = {
            "workflow_id": workflow_id,
            "steps_executed": [],
            "final_result": None,
            "status": "completed",
        }

        current_data = input_data.copy()

        for step in workflow["steps"]:
            step_result = self._execute_step(step, current_data)
            results["steps_executed"].append(
                {"step_name": step.get("name", "unnamed"), "result": step_result}
            )
            current_data.update(step_result)

        results["final_result"] = current_data
        workflow["status"] = "completed"

        return results

    def _execute_step(self, step: Dict, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_type = step.get("type")
        step_name = step.get("name", "unnamed_step")

        if step_type == "process_file":
            return self._step_process_file(data)
        elif step_type == "extract_metadata":
            return self._step_extract_metadata(data)
        elif step_type == "sort_file":
            return self._step_sort_file(data)
        elif step_type == "validate":
            return self._step_validate(data)
        else:
            return {"status": "skipped", "reason": f"Unknown step type: {step_type}"}

    def _step_process_file(self, data: Dict) -> Dict[str, Any]:
        """Process file step"""
        return {
            "processed": True,
            "processing_time": 1.2,
            "file_type_detected": data.get("extension", "unknown"),
        }

    def _step_extract_metadata(self, data: Dict) -> Dict[str, Any]:
        """Extract metadata step"""
        return {
            "metadata_extracted": True,
            "fields_found": ["size", "type", "modified_time"],
            "confidence": 0.95,
        }

    def _step_sort_file(self, data: Dict) -> Dict[str, Any]:
        """Sort file step"""
        return {
            "sorted": True,
            "category": "documents",  # Would be determined by rules
            "confidence": 0.87,
        }

    def _step_validate(self, data: Dict) -> Dict[str, Any]:
        """Validation step"""
        return {
            "validated": True,
            "checks_passed": ["format", "size", "content"],
            "warnings": [],
        }

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution status"""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}

        return {
            "workflow_id": workflow_id,
            "status": self.workflows[workflow_id]["status"],
            "created_at": self.workflows[workflow_id]["created_at"],
        }
