"""
Query engine for Internal Admin.

Handles all database query operations for the admin interface,
including filtering, searching, ordering, and pagination.
"""

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session
from sqlalchemy.orm.strategy_options import selectinload

from .model_admin import ModelAdmin


class QueryResult:
    """
    Container for query results with pagination information.
    """

    def __init__(
        self,
        items: list[Any],
        total_count: int,
        page: int,
        page_size: int
    ) -> None:
        """
        Initialize QueryResult.

        Args:
            items: List of model instances for current page
            total_count: Total number of items across all pages
            page: Current page number (1-based)
            page_size: Number of items per page
        """
        self.items = items
        self.total_count = total_count
        self.page = page
        self.page_size = page_size

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.page_size == 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def previous_page(self) -> int | None:
        """Get previous page number."""
        return self.page - 1 if self.has_previous else None

    @property
    def next_page(self) -> int | None:
        """Get next page number."""
        return self.page + 1 if self.has_next else None


class QueryEngine:
    """
    Handles database queries for admin list views.

    Provides a pipeline for building complex queries with:
    - Base queryset from ModelAdmin
    - Search across multiple fields
    - Filtering by field values
    - Ordering by specified fields
    - Pagination with count optimization
    """

    def __init__(self, model_admin: ModelAdmin) -> None:
        """
        Initialize QueryEngine for a ModelAdmin.

        Args:
            model_admin: ModelAdmin instance to query for
        """
        self.model_admin = model_admin
        self.model = model_admin.model

    def execute_query(
        self,
        session: Session,
        search_query: str | None = None,
        filters: dict[str, Any] | None = None,
        ordering: list[str] | None = None,
        page: int = 1,
        page_size: int | None = None
    ) -> QueryResult:
        """
        Execute complete query pipeline.

        Args:
            session: SQLAlchemy session
            search_query: Text to search for across search_fields
            filters: Dictionary of field -> value filters
            ordering: List of field names for ordering
            page: Page number (1-based)
            page_size: Items per page (defaults to ModelAdmin page_size)

        Returns:
            QueryResult with items and pagination info
        """
        if page_size is None:
            page_size = self.model_admin.get_page_size()

        # Build query pipeline
        query = self._get_base_query(session)
        query = self._apply_search(query, search_query)
        query = self._apply_filters(query, filters)

        # Get total count before pagination
        total_count = query.count()

        # Apply ordering and pagination
        query = self._apply_ordering(query, ordering)
        query = self._apply_eager_loading(query)
        items = self._apply_pagination(query, page, page_size)

        return QueryResult(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    def _get_base_query(self, session: Session) -> Query:
        """
        Get base query from ModelAdmin.

        Args:
            session: SQLAlchemy session

        Returns:
            Base query for the model
        """
        return self.model_admin.get_queryset(session)

    def _apply_search(self, query: Query, search_query: str | None) -> Query:
        """
        Apply text search across search fields.

        Args:
            query: Base query to modify
            search_query: Search string

        Returns:
            Query with search filters applied
        """
        if not search_query or not search_query.strip():
            return query

        search_fields = self.model_admin.get_search_fields()
        if not search_fields:
            return query

        search_term = f"%{search_query.strip()}%"
        search_conditions = []

        for field_name in search_fields:
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                # Use ILIKE for case-insensitive search
                search_conditions.append(field.ilike(search_term))

        if search_conditions:
            query = query.filter(or_(*search_conditions))

        return query

    def _apply_filters(self, query: Query, filters: dict[str, Any] | None) -> Query:
        """
        Apply field-specific filters.

        Args:
            query: Query to modify
            filters: Dictionary of field -> value filters

        Returns:
            Query with filters applied
        """
        if not filters:
            return query

        for field_name, value in filters.items():
            if not hasattr(self.model, field_name):
                continue

            field = getattr(self.model, field_name)

            # Skip empty values
            if value is None or value == "":
                continue

            # Handle different filter types
            if isinstance(value, (list, tuple)):
                # Multiple values - use IN clause
                query = query.filter(field.in_(value))
            elif isinstance(value, bool):
                # Boolean filter
                query = query.filter(field == value)
            else:
                # Exact match filter
                query = query.filter(field == value)

        return query

    def _apply_ordering(self, query: Query, ordering: list[str] | None) -> Query:
        """
        Apply ordering to query.

        Args:
            query: Query to modify
            ordering: List of field names (prefix '-' for descending)

        Returns:
            Query with ordering applied
        """
        order_fields = ordering or self.model_admin.get_ordering()

        for field_spec in order_fields:
            # Handle descending order (field prefixed with '-')
            if field_spec.startswith('-'):
                field_name = field_spec[1:]
                descending = True
            else:
                field_name = field_spec
                descending = False

            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                if descending:
                    query = query.order_by(field.desc())
                else:
                    query = query.order_by(field.asc())

        return query

    def _apply_eager_loading(self, query: Query) -> Query:
        """
        Apply eager loading for foreign key relationships.

        This helps prevent N+1 queries when displaying related objects.

        Args:
            query: Query to modify

        Returns:
            Query with eager loading applied
        """
        # For now, we'll use selectinload for all relationships
        # This can be optimized based on the fields being displayed

        list_display = self.model_admin.get_list_display()

        for field_name in list_display:
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)

                # Check if it's a relationship
                if hasattr(field.property, 'mapper'):
                    # It's a relationship - add selectinload
                    query = query.options(selectinload(getattr(self.model, field_name)))

        return query

    def _apply_pagination(self, query: Query, page: int, page_size: int) -> list[Any]:
        """
        Apply pagination and execute query.

        Args:
            query: Query to paginate
            page: Page number (1-based)
            page_size: Items per page

        Returns:
            List of model instances for the page
        """
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all()

    def get_filter_choices(self, session: Session, field_name: str) -> list[tuple[Any, str]]:
        """
        Get available choices for a filter field.

        Args:
            session: SQLAlchemy session
            field_name: Name of field to get choices for

        Returns:
            List of (value, display_name) tuples
        """
        if not hasattr(self.model, field_name):
            return []

        field = getattr(self.model, field_name)

        # Get distinct values for this field
        distinct_query = session.query(field).distinct().filter(field.is_not(None))

        choices = []
        for (value,) in distinct_query.all():
            # Use string representation as display name
            display_name = str(value) if value is not None else "N/A"
            choices.append((value, display_name))

        # Sort choices by display name
        choices.sort(key=lambda x: x[1])

        return choices
