"""Test-only adapter for Streamlit 1.49 AppTest's st.feedback serializer.
AppTest assumes every ButtonGroup returns a list and has a format_func.
Native st.feedback returns None/int and registers no formatter.
Normalize that testing representation; production widgets are untouched.
"""
from streamlit.testing.v1.element_tree import ButtonGroup
_original_indices = ButtonGroup.indices.fget
def feedback_indices(self):
    if self.format_func is None:
        value=self.value
        if value is None:return []
        if isinstance(value,int):return [value]
        return list(value)
    return _original_indices(self)
ButtonGroup.indices=property(feedback_indices)
