from rest_framework import serializers


class ClassifyTicketInputSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(required=False, max_length=255, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("ticket_id") and (not attrs.get("title") or not attrs.get("description")):
            raise serializers.ValidationError(
                "Provide either 'ticket_id' or both 'title' and 'description'."
            )
        return attrs


class TicketIdInputSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField()
