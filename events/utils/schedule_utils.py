def log_schedule_changes(schedule, changed_fields, original_values=None):
    """Registrar cambios para auditoría"""
    if changed_fields:
        changes = []
        # Mapping for form fields that don't directly match model fields
        field_mapping = {
            'duration_hours': 'duration'
        }

        if original_values is None:
            original_values = {}

        for field in changed_fields:
            # Map form field to model field if necessary
            model_field = field_mapping.get(field, field)

            try:
                # Get old value
                if original_values:
                    old_value = original_values.get(model_field, 'N/A')
                else:
                    old_attr = f'_original_{field}'
                    old_value = getattr(schedule, old_attr, 'N/A')

                # Get new value
                new_value = getattr(schedule, model_field)
                changes.append(f"{field}: {old_value} → {new_value}")
            except AttributeError as e:
                # Skip fields that don't exist on the model
                print(f"Warning: Could not log change for field {field} (mapped to {model_field}): {e}")
                continue

        # Aquí se podría guardar en un log de auditoría
        print(f"[AUDIT] Schedule {schedule.id} changed: {', '.join(changes)}")
