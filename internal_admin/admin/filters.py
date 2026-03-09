"""
Filter system for Internal Admin list views.

Provides filtering capabilities for admin list pages,
including field-based filters and search functionality.
"""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import Boolean, Date, DateTime
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session
from sqlalchemy.sql.sqltypes import TypeDecorator

from .model_admin import ModelAdmin


class BaseFilter(ABC):
    """
    Abstract base class for admin filters.

    Filters provide a way to limit the objects shown in list views
    based on field values or other criteria.
    """

    def __init__(self, field_name: str, title: str | None = None) -> None:
        """
        Initialize filter.

        Args:
            field_name: Name of model field to filter on
            title: Display title for filter (defaults to field name)
        """
        self.field_name = field_name
        self.title = title or field_name.replace('_', ' ').title()

    @abstractmethod
    def get_choices(self, session: Session, model_class: type[Any]) -> list[tuple[Any, str]]:
        """
        Get available filter choices.

        Args:
            session: SQLAlchemy session
            model_class: Model class being filtered

        Returns:
            List of (value, display_name) tuples
        """
        pass

    @abstractmethod
    def apply_filter(self, query: Any, value: Any) -> Any:
        """
        Apply filter to query.

        Args:
            query: SQLAlchemy query to modify
            value: Filter value selected by user

        Returns:
            Modified query
        """
        pass


class FieldFilter(BaseFilter):
    """
    Generic filter for model fields.

    Automatically determines filter behavior based on field type.
    """

    def get_choices(self, session: Session, model_class: type[Any]) -> list[tuple[Any, str]]:
        """Get distinct values for the field."""
        if not hasattr(model_class, self.field_name):
            return []

        field = getattr(model_class, self.field_name)

        # Get distinct non-null values
        distinct_query = session.query(field).distinct().filter(field.is_not(None))

        choices = []
        for (value,) in distinct_query.all():
            display_name = str(value) if value is not None else "N/A"
            choices.append((value, display_name))

        # Sort by display name
        choices.sort(key=lambda x: x[1])

        return choices

    def apply_filter(self, query: Any, value: Any) -> Any:
        """Apply exact match filter."""
        if not value or not hasattr(query.column_descriptions[0]['type'], self.field_name):
            return query

        model_class = query.column_descriptions[0]['type']
        field = getattr(model_class, self.field_name)

        return query.filter(field == value)


class BooleanFilter(BaseFilter):
    """
    Filter for boolean fields with Yes/No choices.
    """

    def get_choices(self, session: Session, model_class: type[Any]) -> list[tuple[Any, str]]:
        """Return Yes/No choices for boolean field."""
        return [
            (True, "Yes"),
            (False, "No"),
        ]

    def apply_filter(self, query: Any, value: Any) -> Any:
        """Apply boolean filter."""
        if value is None:
            return query

        model_class = query.column_descriptions[0]['type']
        field = getattr(model_class, self.field_name)

        # Convert string values to boolean
        if isinstance(value, str):
            bool_value = value.lower() in ('true', '1', 'yes')
        else:
            bool_value = bool(value)

        return query.filter(field == bool_value)


class DateRangeFilter(BaseFilter):
    """
    Filter for date fields with predefined ranges.
    """

    def get_choices(self, session: Session, model_class: type[Any]) -> list[tuple[Any, str]]:
        """Return predefined date range choices."""
        from datetime import datetime, timedelta

        today = datetime.now().date()
        today - timedelta(days=7)
        today - timedelta(days=30)
        today - timedelta(days=365)

        return [
            ("today", "Today"),
            ("week", "Last 7 days"),
            ("month", "Last 30 days"),
            ("year", "Last year"),
        ]

    def apply_filter(self, query: Any, value: Any) -> Any:
        """Apply date range filter."""
        if not value:
            return query

        from datetime import datetime, timedelta

        model_class = query.column_descriptions[0]['type']
        field = getattr(model_class, self.field_name)

        today = datetime.now().date()

        if value == "today":
            return query.filter(field == today)
        elif value == "week":
            week_ago = today - timedelta(days=7)
            return query.filter(field >= week_ago)
        elif value == "month":
            month_ago = today - timedelta(days=30)
            return query.filter(field >= month_ago)
        elif value == "year":
            year_ago = today - timedelta(days=365)
            return query.filter(field >= year_ago)

        return query


class ForeignKeyFilter(BaseFilter):
    """
    Filter for foreign key relationships.
    """

    def __init__(
        self,
        field_name: str,
        title: str | None = None,
        display_field: str = "id"
    ) -> None:
        """
        Initialize foreign key filter.

        Args:
            field_name: Name of foreign key field
            title: Display title
            display_field: Field to use for display names
        """
        super().__init__(field_name, title)
        self.display_field = display_field

    def get_choices(self, session: Session, model_class: type[Any]) -> list[tuple[Any, str]]:
        """Get choices from related model."""
        if not hasattr(model_class, self.field_name):
            return []

        try:
            relationship = self._find_relationship(model_class)
            if relationship is None:
                return []

            related_model = relationship.mapper.class_
            related_mapper = sa_inspect(related_model)
            pk_attr = related_mapper.primary_key[0].key

            label_attr = self.display_field if hasattr(related_model, self.display_field) else None
            if label_attr is None:
                for candidate in ("display_name", "name", "title", "username", "email"):
                    if hasattr(related_model, candidate):
                        label_attr = candidate
                        break

            query = session.query(related_model)
            if label_attr:
                query = query.order_by(getattr(related_model, label_attr).asc())
            else:
                query = query.order_by(getattr(related_model, pk_attr).asc())

            rows = query.limit(200).all()
            choices = []
            for row in rows:
                value = getattr(row, pk_attr)
                if label_attr:
                    label_value = getattr(row, label_attr, None)
                    display = str(label_value) if label_value not in (None, "") else str(value)
                else:
                    display = str(row)
                    if display.startswith("<") and " object at " in display:
                        display = str(value)
                choices.append((value, display))

            return choices
        except Exception:
            return []

    def apply_filter(self, query: Any, value: Any) -> Any:
        """Apply foreign key filter."""
        if not value:
            return query

        model_class = query.column_descriptions[0]['type']
        field = getattr(model_class, self.field_name)

        column = model_class.__table__.columns.get(self.field_name)
        if column is not None:
            column_type = type(column.type)
            if isinstance(column.type, TypeDecorator):
                column_type = type(column.type.impl)
            try:
                if column_type.__name__ in {"Integer", "BigInteger", "SmallInteger"}:
                    value = int(value)
            except (TypeError, ValueError):
                return query

        return query.filter(field == value)

    def _find_relationship(self, model_class: type[Any]) -> Any | None:
        mapper = sa_inspect(model_class)
        for relationship in mapper.relationships:
            for local_column in relationship.local_columns:
                if local_column.key == self.field_name:
                    return relationship
        return None


class FilterManager:
    """
    Manages filters for a ModelAdmin.

    Automatically creates appropriate filters based on model fields
    and ModelAdmin configuration.
    """

    def __init__(self, model_admin: ModelAdmin) -> None:
        """
        Initialize FilterManager.

        Args:
            model_admin: ModelAdmin instance
        """
        self.model_admin = model_admin
        self.model = model_admin.model
        self._filters = {}
        self._create_filters()

    def _create_filters(self) -> None:
        """Create filters based on ModelAdmin configuration."""
        filter_fields = self.model_admin.get_list_filter()

        for field_name in filter_fields:
            filter_obj = self._create_filter_for_field(field_name)
            if filter_obj:
                self._filters[field_name] = filter_obj

    def _create_filter_for_field(self, field_name: str) -> BaseFilter | None:
        """
        Create appropriate filter for a field.

        Args:
            field_name: Name of field to create filter for

        Returns:
            Filter instance or None
        """
        if not hasattr(self.model, field_name):
            return None

        # Find the column in the table
        column = None
        for col in self.model.__table__.columns:
            if col.name == field_name:
                column = col
                break

        if column is None:
            return None

        # Create filter based on column type
        column_type = type(column.type)

        if column_type == Boolean:
            return BooleanFilter(field_name)
        elif column_type in (DateTime, Date):
            return DateRangeFilter(field_name)
        elif column.foreign_keys:
            return ForeignKeyFilter(field_name)
        else:
            return FieldFilter(field_name)

    def get_filters(self) -> dict[str, BaseFilter]:
        """
        Get all configured filters.

        Returns:
            Dictionary of field_name -> Filter
        """
        return self._filters.copy()

    def get_filter(self, field_name: str) -> BaseFilter | None:
        """
        Get filter for specific field.

        Args:
            field_name: Name of field

        Returns:
            Filter instance or None
        """
        return self._filters.get(field_name)

    def get_filter_context(self, session: Session, current_filters: dict[str, Any]) -> dict[str, Any]:
        """
        Get template context for filters.

        Args:
            session: SQLAlchemy session
            current_filters: Currently applied filter values

        Returns:
            Template context for filters
        """
        filter_context = {}

        for field_name, filter_obj in self._filters.items():
            choices = filter_obj.get_choices(session, self.model)
            current_value = current_filters.get(field_name)

            filter_context[field_name] = {
                'title': filter_obj.title,
                'choices': choices,
                'current_value': current_value,
            }

        return filter_context
