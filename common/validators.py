from product import serializers

def age_validator(user):
        birthdate = user.birthdate
        if not birthdate:
            raise serializers.ValidationError("Укажите дату рождения, для создания продукта.")
        age = (date.today() - birthdate).days // 365
        if age < 18:
            raise serializers.ValidationError("Вам должно быть 18 лет, чтобы создать продукт.")