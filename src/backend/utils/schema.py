import warnings

from drf_spectacular.openapi import AutoSchema


class CustomAutoSchema(AutoSchema):
    """Custom AutoSchema to add swagger_topic to tags and handle deprecated endpoints."""

    def get_tags(self):
        tags = []
        try:
            if hasattr(self.view, 'get_serializer'):
                serializer = self.view.get_serializer()
            else:
                serializer = None
        except Exception:
            serializer = None
            warnings.warn(
                '{}.get_serializer() raised an exception during '
                'schema generation. Serializer fields will not be '
                'generated for this view.'.format(self.view.__class__.__name__)
            )

        if hasattr(self.view, 'swagger_topic'):
            tags.append(str(self.view.swagger_topic).title())
        elif serializer and hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
            tags.append(str(serializer.Meta.model._meta.verbose_name_plural).title())
        elif hasattr(self.view, 'model'):
            tags.append(str(self.view.model._meta.verbose_name_plural).title())
        else:
            tags = super().get_tags()  # Use default drf-spectacular behavior

        if not tags:
            warnings.warn(f'Could not determine tags for {self.view.__class__.__name__}')
            tags = ['api']  # Fallback to default value
        return tags

    def is_deprecated(self):
        """Return `True` if this operation is to be marked as deprecated."""
        return getattr(self.view, 'deprecated', False)
