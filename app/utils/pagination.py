from flask import request, url_for
from sqlalchemy.orm import Query
from app.utils.constants import MAX_PAGE_SIZE


class PaginatedResult:
    """
    Class to standardize pagination results.
    Handles paginating SQLAlchemy queries and formatting response.
    Similar to Django REST framework format with only previous and next links.
    """

    def __init__(self, query, page=1, per_page=10, error_out=False):
        """
        Initialize paginator with query and pagination parameters.

        Args:
            query: SQLAlchemy query object
            page: Current page number (default: 1)
            per_page: Items per page (default: 10)
            error_out: Whether to raise 404 when out of range (default: False)
        """
        # Handle invalid pagination parameters
        self.page = max(1, page)  # Ensure page is at least 1
        self.per_page = max(1, per_page)  # Ensure per_page is at least 1
        self.query = query
        self.error_out = error_out

        # Get paginated items
        self.pagination = query.paginate(
            page=self.page, per_page=self.per_page, error_out=error_out
        )

    @property
    def items(self):
        """Get current page items"""
        return self.pagination.items

    @property
    def total(self):
        """Get total number of items"""
        return self.pagination.total

    def to_dict(self, schema, endpoint=None, **kwargs):
        """
        Convert paginated results to Django REST framework-like format.

        Args:
            schema: Marshmallow schema to serialize items
            endpoint: Optional endpoint name for generating URLs
            **kwargs: Additional URL parameters to include in pagination links

        Returns:
            Dictionary with items and pagination metadata (flattened)
        """
        # Serialize items with provided schema
        serialized_items = schema.dump(self.items)

        # Build response in Django REST framework style
        response = {
            "total_items": self.pagination.total,
            "total_pages": self.pagination.pages,
            "current_page": self.page,
            "per_page": self.per_page,
        }

        # Add page navigation links if endpoint is provided
        if endpoint:
            pagination_links = self._get_pagination_links(endpoint, **kwargs)
            response.update(pagination_links)
        else:
            # Always include previous and next links even if no endpoint
            response.update({"previous": None, "next": None})

        # Add items after the pagination metadata
        response["data"] = serialized_items

        return response

    def _get_pagination_links(self, endpoint, **kwargs):
        """
        Generate pagination links for previous and next pages only.
        """
        links = {}

        # Add parameters that should be included in all links
        params = kwargs.copy()
        params["per_page"] = self.per_page

        # Previous page link (null if on first page)
        if self.pagination.has_prev:
            params["page"] = self.page - 1
            links["previous"] = url_for(endpoint, **params, _external=True)
        else:
            links["previous"] = None

        # Next page link (null if on last page)
        if self.pagination.has_next:
            params["page"] = self.page + 1
            links["next"] = url_for(endpoint, **params, _external=True)
        else:
            links["next"] = None

        return links


def paginate(query, schema, endpoint=None, **kwargs):
    """
    Helper function to paginate a query and return standardized results.

    Args:
        query: SQLAlchemy query object
        schema: Marshmallow schema for serializing items
        endpoint: Optional endpoint name for generating navigation URLs
        **kwargs: Additional parameters (page, per_page, and URL params)

    Returns:
        Dictionary with items and pagination metadata in Django REST style
    """
    # Get pagination parameters from request or use defaults
    # Handle invalid inputs by using default values
    try:
        page = int(kwargs.pop("page", request.args.get("page", 1)))
        if page <= 0:
            page = 1
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(kwargs.pop("per_page", request.args.get("per_page", 10)))
        if per_page <= 0:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    # Ensure reasonable limits for pagination
    per_page = min(per_page, MAX_PAGE_SIZE)  # Cap at maximum page size

    # Create paginated result
    paginated_result = PaginatedResult(query, page, per_page)

    # Return formatted result
    return paginated_result.to_dict(schema, endpoint, **kwargs)
