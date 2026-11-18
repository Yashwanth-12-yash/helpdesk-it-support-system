import factory
from apps.accounts.models import User
from apps.departments.models import Department
from apps.teams.models import SupportTeam


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@helpdesk.local")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = User.Role.EMPLOYEE
    job_title = "Staff Member"
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        raw_password = extracted or "StrongPass#2026!"
        self.set_password(raw_password)
        if create:
            self.save(update_fields=["password"])


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Department

    name = factory.Sequence(lambda n: f"IT Department {n}")
    code = factory.Sequence(lambda n: f"IT{n:03d}")
    description = "Enterprise IT Support"
    is_active = True


class SupportTeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SupportTeam

    name = factory.Sequence(lambda n: f"Support Team {n}")
    department = factory.SubFactory(DepartmentFactory)
    description = "L2 Support Queue"
    is_active = True
