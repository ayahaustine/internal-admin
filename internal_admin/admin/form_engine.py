"""
Form engine for Internal Admin.

Handles form generation, validation, and data processing
based on SQLAlchemy model metadata.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session
from sqlalchemy.sql.sqltypes import TypeDecorator

from ..registry import get_registry
from .model_admin import ModelAdmin


@dataclass
class FormField:
    """
    Represents a form field with its metadata.
    """
    name: str
    label: str
    field_type: str
    required: bool
    default_value: Any = None
    choices: list[tuple] | None = None
    readonly: bool = False
    help_text: str | None = None


class FormEngine:
    """
    Generates and processes forms based on SQLAlchemy models.

    Responsibilities:
    - Inspect model columns and generate form fields
    - Map SQLAlchemy types to HTML input types
    - Validate form data and convert types
    - Handle foreign key relationships
    - Process form submissions
    """

    def __init__(self, model_admin: ModelAdmin) -> None:
        """
        Initialize FormEngine for a ModelAdmin.

        Args:
            model_admin: ModelAdmin instance
        """
        self.model_admin = model_admin
        self.model = model_admin.model
        self._type_mapping = self._get_type_mapping()
        self._foreign_key_choice_limit = 200

    def generate_form_fields(self, session: Session, instance: Any | None = None) -> list[FormField]:
        """
        Generate form fields for the model.

        Args:
            session: SQLAlchemy session for foreign key choices
            instance: Optional existing instance for editing

        Returns:
            List of FormField objects
        """
        fields = []
        form_field_names = self.model_admin.get_form_fields()
        readonly_fields = self.model_admin.get_readonly_fields()

        for field_name in form_field_names:
            if not hasattr(self.model, field_name):
                continue

            column = None
            for col in self.model.__table__.columns:
                if col.name == field_name:
                    column = col
                    break

            if column is None:
                continue

            field = self._create_form_field(
                column=column,
                session=session,
                instance=instance,
                readonly=field_name in readonly_fields
            )

            if field:
                fields.append(field)

        return fields

    def _create_form_field(
        self,
        column: Column,
        session: Session,
        instance: Any | None = None,
        readonly: bool = False
    ) -> FormField | None:
        """
        Create a FormField from a SQLAlchemy column.

        Args:
            column: SQLAlchemy column
            session: Database session
            instance: Optional model instance for current values
            readonly: Whether field should be read-only

        Returns:
            FormField or None if field should be skipped
        """
        field_name = column.name

        # Skip primary key for create forms
        if column.primary_key and instance is None:
            return None

        # Get field type mapping
        field_type = self._map_column_type(column)

        # Create label from field name
        label = field_name.replace('_', ' ').title()

        # Determine if required
        required = not column.nullable and column.default is None

        # Get default value
        default_value = None
        if instance:
            default_value = getattr(instance, field_name, None)
        elif column.default is not None:
            if hasattr(column.default, 'arg'):
                default_value = column.default.arg

        # Handle foreign key relationships
        choices = None
        if column.foreign_keys:
            choices = self._get_foreign_key_choices(column, session)
            field_type = "select"

        return FormField(
            name=field_name,
            label=label,
            field_type=field_type,
            required=required,
            default_value=default_value,
            choices=choices,
            readonly=readonly or column.primary_key
        )

    def _map_column_type(self, column: Column) -> str:
        """
        Map SQLAlchemy column type to HTML input type.

        Args:
            column: SQLAlchemy column

        Returns:
            HTML input type string
        """
        column_type = type(column.type)

        # Handle type decorators
        if isinstance(column.type, TypeDecorator):
            column_type = type(column.type.impl)

        return self._type_mapping.get(column_type, "text")

    def _get_type_mapping(self) -> dict[type, str]:
        """
        Get mapping from SQLAlchemy types to HTML input types.

        Returns:
            Dictionary mapping SQLAlchemy types to HTML input types
        """
        return {
            String: "text",
            Text: "textarea",
            Integer: "number",
            Float: "number",
            Boolean: "checkbox",
            DateTime: "datetime-local",
            Date: "date",
        }

    def _get_foreign_key_choices(self, column: Column, session: Session) -> list[tuple]:
        """
        Get choices for a foreign key field.

        Args:
            column: Foreign key column
            session: Database session

        Returns:
            List of (value, label) tuples
        """
        related_model = self._get_related_model_for_column(column)
        if related_model is None:
            return []

        try:
            mapper = sa_inspect(related_model)
            pk_attr = mapper.primary_key[0].key

            label_attr = self._resolve_related_label_attr(related_model)
            query = session.query(related_model)
            if label_attr and hasattr(related_model, label_attr):
                query = query.order_by(getattr(related_model, label_attr).asc())
            else:
                query = query.order_by(getattr(related_model, pk_attr).asc())

            rows = query.limit(self._foreign_key_choice_limit).all()
            return [
                (getattr(row, pk_attr), self._get_related_display_value(row, label_attr, pk_attr))
                for row in rows
            ]
        except Exception:
            return []

    def _get_related_model_for_column(self, column: Column) -> type[Any] | None:
        relationships = sa_inspect(self.model).relationships
        for relationship in relationships:
            if column in relationship.local_columns:
                return relationship.mapper.class_

        try:
            foreign_key = next(iter(column.foreign_keys))
        except StopIteration:
            return None

        referenced_table = foreign_key.column.table
        for model_class in get_registry().get_registered_models().keys():
            if getattr(model_class, "__table__", None) is referenced_table:
                return model_class

        return None

    def _resolve_related_label_attr(self, related_model: type[Any]) -> str | None:
        preferred = ("display_name", "name", "title", "username", "email")
        for attr_name in preferred:
            if hasattr(related_model, attr_name):
                return attr_name
        return None

    def _get_related_display_value(self, row: Any, label_attr: str | None, pk_attr: str) -> str:
        if label_attr:
            value = getattr(row, label_attr, None)
            if value not in (None, ""):
                return str(value)

        value = str(row)
        if value.startswith("<") and " object at " in value:
            return str(getattr(row, pk_attr))
        return value

    def validate_form_data(self, form_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and convert form data.

        Args:
            form_data: Raw form data from request

        Returns:
            Validated and converted data

        Raises:
            ValueError: If validation fails
        """
        validated_data = {}
        errors = []

        form_field_names = self.model_admin.get_form_fields()

        for field_name in form_field_names:
            if not hasattr(self.model, field_name):
                continue

            column = None
            for col in self.model.__table__.columns:
                if col.name == field_name:
                    column = col
                    break

            if column is None:
                continue

            # Skip readonly fields
            if field_name in self.model_admin.get_readonly_fields():
                continue

            # Skip primary key for new objects
            if column.primary_key:
                continue

            raw_value = form_data.get(field_name)

            try:
                validated_value = self._convert_field_value(column, raw_value)
                validated_data[field_name] = validated_value
            except ValueError as e:
                errors.append(f"{field_name}: {str(e)}")

        if errors:
            raise ValueError("; ".join(errors))

        return validated_data

    def _convert_field_value(self, column: Column, raw_value: Any) -> Any:
        """
        Convert and validate a field value.

        Args:
            column: SQLAlchemy column
            raw_value: Raw value from form

        Returns:
            Converted value

        Raises:
            ValueError: If conversion fails
        """
        if raw_value is None or raw_value == "":
            if not column.nullable and column.default is None:
                raise ValueError("This field is required")
            return None

        column_type = type(column.type)

        # Handle type decorators
        if isinstance(column.type, TypeDecorator):
            column_type = type(column.type.impl)

        try:
            if column_type == String or column_type == Text:
                return str(raw_value)
            elif column_type == Integer:
                return int(raw_value)
            elif column_type == Float:
                return float(raw_value)
            elif column_type == Boolean:
                # Handle checkbox values
                return raw_value in (True, "true", "on", "1", 1)
            elif column_type == DateTime:
                if isinstance(raw_value, str):
                    # Parse datetime string
                    return datetime.fromisoformat(raw_value.replace('T', ' '))
                return raw_value
            elif column_type == Date:
                if isinstance(raw_value, str):
                    return datetime.strptime(raw_value, '%Y-%m-%d').date()
                return raw_value
            else:
                return raw_value

        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid value for {column_type.__name__}: {raw_value}") from e

    def populate_instance(self, instance: Any, validated_data: dict[str, Any]) -> None:
        """
        Populate model instance with validated data.

        Args:
            instance: Model instance to populate
            validated_data: Validated form data
        """
        for field_name, value in validated_data.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, value)
