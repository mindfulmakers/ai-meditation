from rest_framework import serializers


class AddValueSerializer(serializers.Serializer):
    payment_method_id = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)

    def validate_amount(self, value):
        if value < 5:
            raise serializers.ValidationError("Amount must be no less than $5.00")
        if value > 200:
            raise serializers.ValidationError("Amount must be less than $200")
        return value


class AddValueHistorySerializer(serializers.Serializer):

    # Use a nice date format for the user
    date = serializers.DateTimeField(format="%A, %B %d, %Y %I:%M%p")  # type: ignore

    amount = serializers.DecimalField(max_digits=5, decimal_places=2)
    status = serializers.CharField()
