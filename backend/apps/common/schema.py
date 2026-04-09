from __future__ import annotations

import copy

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers


def _clone_component(component):
    if component is None:
        return serializers.JSONField(required=False, allow_null=True)

    if isinstance(component, type):
        if issubclass(component, serializers.BaseSerializer):
            return component()
        if issubclass(component, serializers.Field):
            return component()

    if isinstance(component, (serializers.BaseSerializer, serializers.Field)):
        return copy.deepcopy(component)

    raise TypeError(f"Unsupported schema component: {component!r}")


def success_response_schema(name: str, data_component=None):
    return inline_serializer(
        name=name,
        fields={
            "success": serializers.BooleanField(default=True),
            "data": _clone_component(data_component),
            "message": serializers.CharField(default="ok"),
        },
    )


def paginated_success_response_schema(name: str, item_serializer):
    if isinstance(item_serializer, type) and issubclass(item_serializer, serializers.BaseSerializer):
        results_component = item_serializer(many=True)
    elif isinstance(item_serializer, serializers.BaseSerializer):
        results_component = copy.deepcopy(item_serializer)
        results_component.many = True
    else:
        raise TypeError(f"Unsupported paginated serializer: {item_serializer!r}")

    page_component = inline_serializer(
        name=f"{name}Page",
        fields={
            "count": serializers.IntegerField(),
            "next": serializers.URLField(allow_null=True),
            "previous": serializers.URLField(allow_null=True),
            "page": serializers.IntegerField(),
            "pageSize": serializers.IntegerField(),
            "results": results_component,
        },
    )
    return success_response_schema(name, page_component)
