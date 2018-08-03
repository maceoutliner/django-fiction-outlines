"""
Tests for outline views
"""
import pytest
import django
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from test_plus.test import TestCase
from fiction_outlines.models import Series, Character, CharacterInstance, Outline
from fiction_outlines.models import Location, LocationInstance, Arc
from fiction_outlines.models import ArcElementNode, StoryElementNode

# Create your test here.


class FictionOutlineViewTestCase(TestCase):
    """
    An abstract class to speed up setup of test cases.
    """

    def setUp(self):
        """
        Generic data setup for test cases.
        """
        self.user1 = self.make_user("u1")
        self.user2 = self.make_user("u2")
        self.user3 = self.make_user("u3")
        self.s1 = Series(title="Urban Fantasy Series", user=self.user1)
        self.s1.save()
        self.s2 = Series(title="Space Opera Trilogy", user=self.user1)
        self.s2.save()
        self.s3 = Series(title="Mil-SF series", user=self.user2)
        self.s3.save()
        self.c1 = Character(name="John Doe", tags="ptsd, anxiety", user=self.user1)
        self.c2 = Character(name="Jane Doe", tags="teen, magical", user=self.user1)
        self.c1.save()
        self.c2.save()
        self.c1.series.add(self.s1)
        self.c2.series.add(self.s2)
        self.c3 = Character(name="Michael Smith", user=self.user2)
        self.c4 = Character(name="Eliza Doolittle", tags="muderess", user=self.user2)
        self.c3.save()
        self.c3.series.add(self.s3)
        self.c4.save()
        self.o1 = Outline(title="OOGA", user=self.user1)
        self.o2 = Outline(title="Chicken Little", user=self.user1)
        self.o3 = Outline(title="Dancing Rabbit", user=self.user2)
        self.o1.save()
        self.o2.save()
        self.o3.save()
        self.c1int = CharacterInstance(outline=self.o1, character=self.c1)
        self.c2int = CharacterInstance(outline=self.o1, character=self.c2)
        self.c1int2 = CharacterInstance(outline=self.o2, character=self.c1)
        self.c3int = CharacterInstance(outline=self.o3, character=self.c3)
        self.c1int.save()
        self.c2int.save()
        self.c1int2.save()
        self.c3int.save()
        self.l1 = Location(name="Abandoned Warehouse", user=self.user1)
        self.l1.save()
        self.l1.series.add(self.s1)
        self.l1int = LocationInstance(outline=self.o1, location=self.l1)
        self.l1int.save()
        self.l2 = Location(name="Ghost Ship", user=self.user1)
        self.l2.save()
        self.l2.series.add(self.s2)
        self.l2int = LocationInstance(outline=self.o1, location=self.l2)
        self.l2int.save()
        self.l1int2 = LocationInstance(outline=self.o2, location=self.l1)
        self.l1int2.save()
        self.l3 = Location(name="Haunted house", user=self.user2)
        self.l3.save()
        self.l3.series.add(self.s2)
        self.l3int = LocationInstance(outline=self.o1, location=self.l3)
        self.l3int.save()
        self.l4 = Location(name="The damn bar", tags="humor", user=self.user2)
        self.l4.save()
        self.l4int = LocationInstance(outline=self.o3, location=self.l4)
        self.l4int.save()
        self.arc1 = self.o1.create_arc(name="Coming of age", mace_type="character")
        self.arc2 = self.o1.create_arc(name="dragon invastion", mace_type="event")
        self.arc3 = self.o2.create_arc(name="AIs turn against us", mace_type="event")
        self.arc4 = self.o2.create_arc(
            name="Overcome alien predjudice", mace_type="character"
        )
        self.arc5 = self.o3.create_arc(
            name="Travel to fairie and get back", mace_type="milieu"
        )

    def response_forbidden(self):
        """
        We add a method to validate that this follows the proper behavior. Should only be used in tests
        with authenticated users.
        """
        if django.VERSION < (2, 1):
            return self.response_302()
        return self.response_403()


class SeriesViewTest(FictionOutlineViewTestCase):
    """
    Tests views associated with Series model
    """

    def test_view_requires_signin(self):
        """
        Ensure that attempts to load this view without auth result in 302.
        """
        self.assertLoginRequired("fiction_outlines:series_list")

    def test_view_shows_only_users_series(self):
        """
        Test that a user can only see their own series.
        """
        for user in [self.user1, self.user2, self.user3]:
            with self.login(username=user.username):
                self.assertGoodView("fiction_outlines:series_list")
                series_list = self.get_context("series_list")
                assert len(series_list) == Series.objects.filter(user=user).count()
                for series in series_list:
                    assert series.user == user
        with self.login(username=self.user3.username):
            self.get("fiction_outlines:series_list")
            assert not self.get_context("series_list")
            print(self.last_response.content)
            self.assertResponseContains(
                "You do not have any series defined yet.", html=False
            )


class SeriesCreateViewTest(FictionOutlineViewTestCase):
    """
    Tests for series creation.
    """

    def test_view_requires_signin(self):
        """
        Ensure that only authenticated users can access page.
        """
        self.assertLoginRequired("fiction_outlines:series_create")

    def test_basic_page_loading(self):
        """
        Verify the basic get request loads the form appropriately.
        """
        for user in [self.user1, self.user2, self.user3]:
            with self.login(username=user.username):
                self.assertGoodView("fiction_outlines:series_create")
                self.assertInContext("form")

    def test_series_creation(self):
        """
        Ensure that the post creates the object successfully.
        """
        series_before = Series.objects.filter(user=self.user1).count()
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:series_create",
                data={
                    "title": "Monkeys of Heaven",
                    "description": "The second trilogy in my astral primates cycle.",
                    "tags": "primates, astral",
                },
            )
            series_after = Series.objects.filter(user=self.user1).count()
            assert series_after - series_before == 1
            latest = Series.objects.filter(user=self.user1).latest("created")
            assert latest.title == "Monkeys of Heaven"


class SeriesUpdateViewTest(FictionOutlineViewTestCase):
    """
    Test ability to update series.
    """

    def test_view_requires_login(self):
        """
        You have to be authenticated.
        """
        self.assertLoginRequired("fiction_outlines:series_update", series=self.s1.pk)

    def test_from_loads_correctly(self):
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:series_update", series=self.s1.pk)
            self.assertInContext("form")
            self.assertInContext("series")

    def test_object_permissions_honored(self):
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:series_update", series=self.s1.pk)
                self.response_forbidden()
                self.post(
                    "fiction_outlines:series_update",
                    series=self.s1.pk,
                    data={"title": "war of cats"},
                )
                self.response_forbidden()
                assert "war of cats" != Series.objects.get(pk=self.s1.pk).title

    def test_valid_edit(self):
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:series_update",
                series=self.s1.pk,
                data={
                    "title": "Giraffe country",
                    "description": "Elaborate plot device",
                    "tags": "forgive me, we did not know",
                },
            )
            test_series = Series.objects.get(pk=self.s1.pk)
            assert test_series.title == "Giraffe country"


class SeriesDeleteViewTest(FictionOutlineViewTestCase):
    """
    Test the series delete view.
    """

    def test_requires_login(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired("fiction_outlines:series_delete", series=self.s1.pk)

    def test_object_permissions(self):
        """
        Ensure that users without permissions for the object cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:series_delete", series=self.s1.pk)
                self.response_forbidden()
                self.post("fiction_outlines:series_delete", series=self.s1.pk)
                assert Series.objects.get(pk=self.s1.pk)  # Still here.

    def test_normal_workflow(self):
        """
        Test that authorized user can delete correctly
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:series_delete", series=self.s1.pk)
            self.assertInContext("series")
            assert self.s1 == self.get_context("series")
            self.post("fiction_outlines:series_delete", series=self.s1.pk)
            with pytest.raises(ObjectDoesNotExist):
                Series.objects.get(pk=self.s1.pk)


class CharacterListViewTest(FictionOutlineViewTestCase):
    """
    Test cases around the list view for characters and character instances.
    """

    def test_login_required(self):
        """
            Must be authenticated user to access.
            """
        self.assertLoginRequired("fiction_outlines:character_list")
        for character in [self.c1, self.c2, self.c3, self.c4]:
            self.assertLoginRequired(
                "fiction_outlines:character_instance_list", character=character.pk
            )

    def test_character_restricted_by_user(self):
        """
        Assert that a user can only see their own data.
        """
        for user in [self.user1, self.user2]:
            with self.login(username=user.username):
                self.assertGoodView("fiction_outlines:character_list")
                character_list = self.get_context("character_list")
                assert (
                    len(character_list) == Character.objects.filter(user=user).count()
                )
                for character in character_list:
                    assert character.user == user
        with self.login(username=self.user3.username):
            self.get("fiction_outlines:character_list")
            self.assertResponseContains(
                "You don't have any characters defined yet.", html=False
            )

    def test_character_instance_view_restriction(self):
        """
        Ensure that only a user with read access to the character can see list.
        """
        with self.login(username=self.user3.username):
            for character in [self.c1, self.c2, self.c3, self.c4]:
                print(
                    "Now evaluating character: %s <%s>" % (character.name, character.pk)
                )
                self.get(
                    "fiction_outlines:character_instance_list", character=character.pk
                )
                self.response_forbidden()
        with self.login(username=self.user2.username):
            for character in [self.c1, self.c2]:
                self.get(
                    "fiction_outlines:character_instance_list", character=character.pk
                )
                self.response_forbidden()
            for character in [self.c3, self.c4]:
                self.assertGoodView(
                    "fiction_outlines:character_instance_list", character=character.pk
                )
                charints = self.get_context("character_instance_list")
                assert (
                    len(charints)
                    == CharacterInstance.objects.filter(character=character).count()
                )
                for cint in charints:
                    assert cint.character == character
        with self.login(username=self.user1.username):
            for character in [self.c1, self.c2]:
                self.assertGoodView(
                    "fiction_outlines:character_instance_list", character=character.pk
                )
                charints = self.get_context("character_instance_list")
                assert (
                    len(charints)
                    == CharacterInstance.objects.filter(character=character).count()
                )
                for cint in charints:
                    assert cint.character == character
            for character in [self.c3, self.c4]:
                self.get(
                    "fiction_outlines:character_instance_list", character=character.pk
                )
                self.response_forbidden()


class CharacterCreateTestCase(FictionOutlineViewTestCase):
    """
    Tests for character creation view.
    """

    def test_requires_login(self):
        """
        You have to be logged in!
        """
        self.assertLoginRequired("fiction_outlines:character_create")

    def test_character_create(self):
        """
        Test character creation form works, and that
        users can't feed it invalid data.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:character_create")
            before_create = Character.objects.filter(user=self.user1).count()
            self.post(
                "fiction_outlines:character_create",
                data={
                    "name": "Mary Sue",
                    "description": "She is awesome at everything she does.",
                    "tags": "badass, not lame",
                    "series": self.s3.pk,
                },
            )
            self.response_200()
            after_create = Character.objects.filter(user=self.user1).count()
            assert before_create == after_create
            form = self.get_context("form")
            assert len(form.errors) == 1
            self.post(
                "fiction_outlines:character_create",
                data={
                    "name": "Mary Sue",
                    "description": "She is awesome at everything she does.",
                    "tags": "badass, not lame",
                    "series": self.s1.pk,
                },
            )
            self.response_302()
            assert (
                Character.objects.filter(user=self.user1).count() - before_create == 1
            )
            assert (
                "Mary Sue"
                == Character.objects.filter(user=self.user1).latest("created").name
            )


class CharacterDetailTestCase(FictionOutlineViewTestCase):
    """
    Tests for charscter detail view
    """

    def test_requries_login(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:character_detail", character=self.c1.pk
        )

    def test_object_permissions(self):
        """
        Prevent unauthorized users from accessing.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:character_detail", character=self.c1.pk)
                self.response_forbidden()

    def test_normal_view(self):
        """
        Ensure normal owner of character can access it.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:character_detail", character=self.c1.pk
            )
            self.assertInContext("character")
            character = self.get_context("character")
            assert character.name == self.c1.name


class CharacterUpdateTestCase(FictionOutlineViewTestCase):
    """
    Tests for character update view.
    """

    def test_requires_login(self):
        """
        Must be authenticated
        """
        self.assertLoginRequired(
            "fiction_outlines:character_update", character=self.c1.pk
        )

    def test_access_requires_object_permission(self):
        """
        Only users with edit rights for characters can access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:character_update", character=self.c1.pk)
                self.response_forbidden()
                self.post(
                    "fiction_outlines:character_update",
                    character=self.c1.pk,
                    data={
                        "name": "Doctor Nick",
                        "description": "Hi everybody!",
                        "tags": "discount",
                        "series": self.s1.pk,
                    },
                )
                self.response_forbidden()

                assert (
                    self.c1.name
                    == Character.objects.get(pk=self.c1.pk).name
                    == "John Doe"
                )

    def test_normal_workflow(self):
        """
        Test workflow for valid user.
        """
        assert self.user1.has_perm("fiction_outlines.edit_character", self.c1)
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:character_update", character=self.c1.pk
            )
            self.assertInContext("form")
            self.post(
                "fiction_outlines:character_update",
                character=self.c1.pk,
                data={
                    "name": "Doctor Nick",
                    "description": "Hi everybody!",
                    "tags": "discount",
                    "series": self.s3.pk,
                },
            )
            form = self.get_context("form")
            assert len(form.errors) == 1
            self.post(
                "fiction_outlines:character_update",
                character=self.c1.pk,
                data={
                    "name": "Doctor Nick",
                    "description": "Hi everybody!",
                    "tags": "discount",
                    "series": self.s1.pk,
                },
            )
            assert Character.objects.get(pk=self.c1.pk).name == "Doctor Nick"


class CharacterDeleteViewTest(FictionOutlineViewTestCase):
    """
    Test the series delete view.
    """

    def test_requires_login(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:character_delete", character=self.c1.pk
        )

    def test_object_permissions(self):
        """
        Ensure that users without permissions for the object cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:character_delete", character=self.c1.pk)
                self.response_forbidden()
                self.post("fiction_outlines:character_delete", character=self.c1.pk)
                assert Character.objects.get(pk=self.c1.pk)  # Still here.

    def test_normal_workflow(self):
        """
        Test that authorized user can delete correctly
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:character_delete", character=self.c1.pk
            )
            self.assertInContext("character")
            assert self.c1 == self.get_context("character")
            self.post("fiction_outlines:character_delete", character=self.c1.pk)
            with pytest.raises(ObjectDoesNotExist):
                Character.objects.get(pk=self.c1.pk)


class CharacterInstanceDetailTest(FictionOutlineViewTestCase):
    """
    Tests for character instance detail view.
    """

    def test_requires_login(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:character_instance_detail",
            character=self.c1.pk,
            instance=self.c1int.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:character_instance_detail",
                    character=self.c1.pk,
                    instance=self.c1int.pk,
                )
                self.response_forbidden()

    def test_normal_workflow(self):
        """
        Test that authorized user can access correctly.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:character_instance_detail",
                character=self.c1.pk,
                instance=self.c1int.pk,
            )
            self.assertInContext("character_instance")
            assert self.c1int == self.get_context("character_instance")


class CharacterInstanceCreateTest(FictionOutlineViewTestCase):
    """
    Test update view for character instance.
    """

    def setUp(self):
        super().setUp()
        self.local_outline = Outline(
            title="Local Outline", description="Heeeeeeey", user=self.user1
        )
        self.local_outline.save()

    def test_requires_login(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:character_instance_create", character=self.c1.pk
        )

    def test_object_permissions(self):
        """
        Ensure users without permissions cannot access or change the record.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:character_instance_create", character=self.c1.pk
                )
                self.response_forbidden()
                before_create = self.c1.characterinstance_set.count()

                self.post(
                    "fiction_outlines:character_instance_create",
                    character=self.c1.pk,
                    data={
                        "outline": self.local_outline.pk,
                        "main_character": True,
                        "pov_character": False,
                        "protagonist": False,
                        "antagonist": True,
                        "obstacle": False,
                        "villain": False,
                    },
                )
                assert (
                    before_create
                    == CharacterInstance.objects.filter(character=self.c1).count()
                )

    def test_invalid_form(self):
        """
        Test authorized user trying to submit invalid outline choice, or duplicate outline choice.
        """
        before_create = self.c1.characterinstance_set.count()
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:character_instance_create",
                character=self.c1.pk,
                data={
                    "outline": self.o3.pk,
                    "main_character": True,
                    "pov_character": False,
                    "protagonist": False,
                    "antagonist": True,
                    "obstacle": False,
                    "villain": False,
                },
            )
            self.response_200()
            form = self.get_context("form")
            assert len(form.errors) == 1
            assert (
                before_create
                == CharacterInstance.objects.filter(character=self.c1).count()
            )
            try:
                with transaction.atomic():
                    with pytest.raises(IntegrityError):
                        self.post(
                            "fiction_outlines:character_instance_create",
                            character=self.c1.pk,
                            data={
                                "outline": self.o2.pk,
                                "main_character": True,
                                "pov_character": False,
                                "protagonist": False,
                                "antagonist": True,
                                "obstacle": False,
                                "villain": False,
                            },
                        )
            except IntegrityError:
                pass
            assert (
                before_create
                == CharacterInstance.objects.filter(character=self.c1).count()
            )

    def test_valid_form(self):
        """
        Ensure authorized user can make allowed changes.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:character_instance_create", character=self.c1.pk
            )
            self.assertInContext("form")
            before_create = self.c1.characterinstance_set.count()
            self.post(
                "fiction_outlines:character_instance_create",
                character=self.c1.pk,
                data={
                    "outline": self.local_outline.pk,
                    "main_character": True,
                    "pov_character": False,
                    "protagonist": False,
                    "antagonist": True,
                    "obstacle": False,
                    "villain": False,
                },
            )
            assert (
                CharacterInstance.objects.filter(character=self.c1).count()
                - before_create
                == 1
            )


class CharacterInstanceUpdateTest(FictionOutlineViewTestCase):
    """
    Test update view for character instance.
    """

    def test_requires_login(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:character_instance_update",
            character=self.c1.pk,
            instance=self.c1int.pk,
        )

    def test_object_permissions(self):
        """
        Ensure users without permissions cannot access or change the record.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:character_instance_update",
                    character=self.c1.pk,
                    instance=self.c1int.pk,
                )
                self.response_forbidden()

                assert not self.c1int.main_character
                self.post(
                    "fiction_outlines:character_instance_update",
                    character=self.c1.pk,
                    instance=self.c1int.pk,
                    data={
                        "outline": self.o1.pk,
                        "main_character": True,
                        "pov_character": False,
                        "protagonist": False,
                        "antagonist": True,
                        "obstacle": False,
                        "villain": False,
                    },
                )
                assert (
                    self.c1int.main_character
                    == CharacterInstance.objects.get(pk=self.c1int.pk).main_character
                )

    def test_invalid_form(self):
        """
        Test authorized user trying to submit invalid outline choice, or duplicate outline choice.
        """
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:character_instance_update",
                character=self.c1.pk,
                instance=self.c1int.pk,
                data={
                    "outline": self.o3.pk,
                    "main_character": True,
                    "pov_character": False,
                    "protagonist": False,
                    "antagonist": True,
                    "obstacle": False,
                    "villain": False,
                },
            )
            self.response_200()
            form = self.get_context("form")
            assert len(form.errors) == 1
            try:
                with transaction.atomic():
                    with pytest.raises(IntegrityError):
                        self.post(
                            "fiction_outlines:character_instance_update",
                            character=self.c1.pk,
                            instance=self.c1int.pk,
                            data={
                                "outline": self.o2.pk,
                                "main_character": True,
                                "pov_character": False,
                                "protagonist": False,
                                "antagonist": True,
                                "obstacle": False,
                                "villain": False,
                            },
                        )
            except IntegrityError:
                pass
            assert (
                self.c1int.main_character
                == CharacterInstance.objects.get(pk=self.c1int.pk).main_character
            )

    def test_valid_form(self):
        """
        Ensure authorized user can make allowed changes.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:character_instance_update",
                character=self.c1.pk,
                instance=self.c1int.pk,
            )
            self.assertInContext("form")
            assert self.c1int == self.get_context("character_instance")
            self.post(
                "fiction_outlines:character_instance_update",
                character=self.c1.pk,
                instance=self.c1int.pk,
                data={
                    "outline": self.o1.pk,
                    "main_character": True,
                    "pov_character": False,
                    "protagonist": False,
                    "antagonist": True,
                    "obstacle": False,
                    "villain": False,
                },
            )
            test_cint = CharacterInstance.objects.get(pk=self.c1int.pk)
            assert test_cint.main_character
            assert test_cint.antagonist


class CharacterInstanceDeleteTest(FictionOutlineViewTestCase):
    """
    Tests for character instance deletion.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:character_instance_delete",
            character=self.c1.pk,
            instance=self.c1int.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:character_instance_delete",
                    character=self.c1.pk,
                    instance=self.c1int.pk,
                )
                self.response_forbidden()

                self.post(
                    "fiction_outlines:character_instance_delete",
                    character=self.c1.pk,
                    instance=self.c1int.pk,
                )
                assert CharacterInstance.objects.get(pk=self.c1int.pk)

    def test_normal_workflow(self):
        """
        Ensure authorized user can access and delete.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:character_instance_delete",
                character=self.c1.pk,
                instance=self.c1int.pk,
            )
            assert self.c1int == self.get_context("character_instance")
            self.post(
                "fiction_outlines:character_instance_delete",
                character=self.c1.pk,
                instance=self.c1int.pk,
            )
            with pytest.raises(ObjectDoesNotExist):
                CharacterInstance.objects.get(pk=self.c1int.pk)


class OutlineListTestCase(FictionOutlineViewTestCase):
    """
    Tests for outline outline list view.
    """

    def test_view_requires_login(self):
        """
        Ensure that login is required.
        """
        self.assertLoginRequired("fiction_outlines:outline_list")

    def test_user_restriction_for_outlines(self):
        """
        Assert that the outline list is correctly restricted by user.
        """
        for user in [self.user1, self.user2, self.user3]:
            with self.login(username=user.username):
                self.assertGoodView("fiction_outlines:outline_list")
                self.get("fiction_outlines:outline_list")
                outline_list = self.get_context("outline_list")
                assert len(outline_list) == Outline.objects.filter(user=user).count()
                for outline in outline_list:
                    assert outline.user == user
                    if outline.series:
                        for series in outline.series.all():
                            self.assertResponseContains(series.title)
        with self.login(username=self.user3.username):
            self.get("fiction_outlines:outline_list")
            self.assertResponseContains("You don't have any outlines yet.", html=False)


class OutlineDetailTestCase(FictionOutlineViewTestCase):
    """
    Tests outline detail view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired("fiction_outlines:outline_detail", outline=self.o1.pk)

    def test_object_permissions(self):
        """
        Ensure that object permissions are obeyed.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:outline_detail", outline=self.o1.pk)
                self.response_forbidden()

    def test_normal_workflow(self):
        """
        Authorized users should be able to access.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:outline_detail", outline=self.o1.pk)
            self.assertInContext("outline")
            assert self.o1 == self.get_context("outline")


class OutlineCreateTestCase(FictionOutlineViewTestCase):
    """
    Test outline creation view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired("fiction_outlines:outline_create")

    def test_form_load(self):
        """
        Test form loading works correctly.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:outline_create")
            self.assertInContext("form")

    def test_form_submittal_with_invalid_series(self):
        """
        Try to create an outline, but tie it to a series the user
        lacks object permissions to access.
        """
        with self.login(username=self.user1.username):
            before = Outline.objects.filter(user=self.user1).count()
            self.post(
                "fiction_outlines:outline_create",
                data={
                    "title": "My Opus",
                    "description": "Not the penguin. A work of art",
                    "tags": "antartica",
                    "series": self.s3.pk,
                },
            )
            self.response_200()
            self.assertInContext("form")
            form = self.get_context("form")
            assert len(form.errors) == 1
            assert before == Outline.objects.filter(user=self.user1).count()

    def test_valid_form_submittal(self):
        """
        Test a valid creation request.
        """
        with self.login(username=self.user1.username):
            before = Outline.objects.filter(user=self.user1).count()
            self.post(
                "fiction_outlines:outline_create",
                data={
                    "title": "My Opus",
                    "description": "Not the penguin. A work of art",
                    "tags": "antartica",
                    "series": self.s2.pk,
                },
            )
            self.response_302()
            assert Outline.objects.filter(user=self.user1).count() - before == 1
            assert (
                "My Opus"
                == Outline.objects.filter(user=self.user1).latest("created").title
            )


class OutlineUpdateTestCase(FictionOutlineViewTestCase):
    """
    Test for outline editing view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired("fiction_outlines:outline_update", outline=self.o1.pk)

    def test_object_permissions(self):
        """
        Ensure that unathorized users cannot access the view or submit an update.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:outline_update", outline=self.o1.pk)
                self.response_forbidden()

                self.post(
                    "fiction_outlines:outline_update",
                    outline=self.o1.pk,
                    data={
                        "title": "Malicious Edit",
                        "description": "Hisssssssssss",
                        "tags": "pwned",
                        "series": self.s1.pk,
                    },
                )
                assert self.o1.title == Outline.objects.get(pk=self.o1.pk).title

    def test_invalid_form_submittal(self):
        """
        Tests that an authorized user cannot update the record to an invalid series.
        """
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:outline_update",
                outline=self.o1.pk,
                data={
                    "title": "Monkey, Private Investigations",
                    "description": "He gets to the bottom of the case",
                    "tags": "simian",
                    "series": self.s3.pk,
                },
            )
            self.response_200()
            self.assertInContext("form")
            form = self.get_context("form")
            assert len(form.errors) == 1
            assert self.o1.title == Outline.objects.get(pk=self.o1.pk).title

    def test_valid_form_submission(self):
        """
        Test valid form submission
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:outline_update", outline=self.o1.pk)
            self.assertInContext("form")
            self.assertInContext("outline")
            assert self.o1 == self.get_context("outline")
            self.post(
                "fiction_outlines:outline_update",
                outline=self.o1.pk,
                data={
                    "title": "Grandpa digs in snow",
                    "description": "Did you know that writing tests can be a *bit* boring?",
                    "tags": "no sleep, clowns",
                    "series": self.s2.pk,
                },
            )
            self.response_302()
            assert "Grandpa digs in snow" == Outline.objects.get(pk=self.o1.pk).title


class OutlineDeleteTest(FictionOutlineViewTestCase):
    """
    Test delete view for outlines.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired("fiction_outlines:outline_delete", outline=self.o1.pk)

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access view.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:outline_delete", outline=self.o1.pk)
                self.response_forbidden()

                self.post("fiction_outlines:outline_delete", outline=self.o1.pk)
                assert Outline.objects.get(pk=self.o1.pk)

    def test_normal_workflow(self):
        """
        Ensure authorized user can access and delete.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:outline_delete", outline=self.o1.pk)
            self.assertInContext("outline")
            assert self.o1 == self.get_context("outline")
            self.post("fiction_outlines:outline_delete", outline=self.o1.pk)
            with pytest.raises(ObjectDoesNotExist):
                Outline.objects.get(pk=self.o1.pk)


class LocationListViewTestCase(FictionOutlineViewTestCase):
    """
    Test cases for the Location List View, and Location Instance list view.
    """

    def test_login_required(self):
        """
        Assert login required to see list.
        """
        self.assertLoginRequired("fiction_outlines:location_list")
        for loc in [self.l1, self.l2, self.l3, self.l4]:
            self.assertLoginRequired(
                "fiction_outlines:location_instance_list", location=loc.pk
            )

    def test_locations_restricted_by_user(self):
        """
        Assert that location list is restricted by user.
        """
        for user in [self.user1, self.user2, self.user3]:
            with self.login(username=user.username):
                self.assertGoodView("fiction_outlines:location_list")
                self.get("fiction_outlines:location_list")
                locations = self.get_context("location_list")
                assert len(locations) == Location.objects.filter(user=user).count()
                for location in locations:
                    assert location.user == user
                    for series in location.series.all():
                        self.assertResponseContains(series.title, html=False)
        with self.login(username=self.user3.username):
            self.get("fiction_outlines:location_list")
            self.assertResponseContains(
                "You don't have any locations defined yet.", html=False
            )

    def test_location_instance_list_limited_by_object_permission(self):
        """
        Assert that user cannot access location instance list unless they have
        view permissions for the location itself.
        """
        with self.login(username=self.user3.username):
            for loc in [self.l1, self.l2, self.l3, self.l4]:
                self.get("fiction_outlines:location_instance_list", location=loc.pk)
                self.response_forbidden()
        with self.login(username=self.user2.username):
            for loc in [self.l3, self.l4]:
                self.assertGoodView(
                    "fiction_outlines:location_instance_list", location=loc.pk
                )
                instances = self.get_context("location_instance_list")
                assert (
                    len(instances)
                    == LocationInstance.objects.filter(location=loc).count()
                )
                for lint in instances:
                    assert lint.location == loc
            for loc in [self.l1, self.l2]:
                self.get("fiction_outlines:location_instance_list", location=loc.pk)
                self.response_forbidden()
        with self.login(username=self.user1.username):
            for loc in [self.l1, self.l2]:
                self.assertGoodView(
                    "fiction_outlines:location_instance_list", location=loc.pk
                )
                instances = self.get_context("location_instance_list")
                assert (
                    len(instances) == LocationInstance.objects.filter(location=loc).count()
                )
                for lint in instances:
                    assert lint.location == loc
            for loc in [self.l3, self.l4]:
                self.get("fiction_outlines:location_instance_list", location=loc.pk)
                self.response_forbidden()


class LocationDetailViewTest(FictionOutlineViewTestCase):
    """
    Tests for location detail view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:location_detail", location=self.l1.pk
        )

    def test_object_permissions(self):
        """
        Prevent unauthorized users from accessing.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:location_detail", location=self.l1.pk)
                self.response_forbidden()

    def test_normal_workflow(self):
        """
        Make sure view loads correctly for authorized user.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:location_detail", location=self.l1.pk)
            self.assertInContext("location")
            assert self.l1 == self.get_context("location")


class LocationCreateTestCase(FictionOutlineViewTestCase):
    """
    Tests for location creation view.
    """

    def test_requires_login(self):
        """
        You have to be logged in!
        """
        self.assertLoginRequired("fiction_outlines:location_create")

    def test_location_create(self):
        """
        Test character creation form works, and that
        users can't feed it invalid data.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:location_create")
            before_create = Location.objects.filter(user=self.user1).count()
            self.post(
                "fiction_outlines:character_create",
                data={
                    "name": "Margaritaville",
                    "description": "Missing a shaker of salt.",
                    "tags": "your dad, parrothead",
                    "series": self.s3.pk,
                },
            )
            self.response_200()
            after_create = Location.objects.filter(user=self.user1).count()
            assert before_create == after_create
            form = self.get_context("form")
            assert len(form.errors) == 1
            self.post(
                "fiction_outlines:location_create",
                data={
                    "name": "Margaritaville",
                    "description": "Missing a shaker of salt.",
                    "tags": "your dad, parrothead",
                    "series": self.s1.pk,
                },
            )
            self.response_302()
            assert Location.objects.filter(user=self.user1).count() - before_create == 1
            assert (
                "Margaritaville" == Location.objects.filter(user=self.user1).latest("created").name
            )


class LocationUpdateTest(FictionOutlineViewTestCase):
    """
    Tests for location update views.
    """

    def test_requires_login(self):
        """
        You must be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:location_update", location=self.l1.pk
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access or edit.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:location_update", location=self.l1.pk)
                self.response_forbidden()

                self.post(
                    "fiction_outlines:location_update",
                    location=self.l1.pk,
                    data={
                        "name": "Tactical Blanket Fort",
                        "description": "So cozy, and safe.",
                        "tags": "cuddles",
                        "series": self.s2.pk,
                    },
                )
                assert self.l1.name == Location.objects.get(pk=self.l1.pk).name

    def test_invalid_form(self):
        """
        Ensure that authorized user cannot make invalid form submission.
        """
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:location_update",
                location=self.l1.pk,
                data={
                    "name": "Tactical Blanket Fort",
                    "description": "So cozy, and safe.",
                    "tags": "cuddles",
                    "series": self.s3.pk,
                },
            )
            self.response_200()
            form = self.get_context("form")
            assert len(form.errors) == 1
            assert self.l1.name == Location.objects.get(pk=self.l1.pk).name

    def test_valid_form_submission(self):
        """
        Test the proper workflow.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:location_update", location=self.l1.pk)
            self.assertInContext("location")
            self.assertInContext("form")
            assert self.l1 == self.get_context("location")
            self.post(
                "fiction_outlines:location_update",
                location=self.l1.pk,
                data={
                    "name": "Tactical Blanket Fort",
                    "description": "So cozy, and safe.",
                    "tags": "cuddles",
                    "series": self.s2.pk,
                },
            )
            self.response_302()
            assert "Tactical Blanket Fort" == Location.objects.get(pk=self.l1.pk).name


class LocationDeleteViewTest(FictionOutlineViewTestCase):
    """
    Tests for location delete view.
    """

    def test_requires_login(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:location_delete", location=self.l1.pk
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:location_delete", location=self.l1.pk)
                self.response_forbidden()

                self.post("fiction_outlines:location_delete", location=self.l1.pk)
                assert Location.objects.get(pk=self.l1.pk)

    def test_normal_workflow(self):
        """
        Test with authorized user.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:location_delete", location=self.l1.pk)
            self.assertInContext("location")
            assert self.l1 == self.get_context("location")
            self.post("fiction_outlines:location_delete", location=self.l1.pk)
            with pytest.raises(ObjectDoesNotExist):
                Location.objects.get(pk=self.l1.pk)


class LocationInstanceDetailTest(FictionOutlineViewTestCase):
    """
    Test detail view of location instance.
    """

    def test_login_required(self):
        self.assertLoginRequired(
            "fiction_outlines:location_instance_detail",
            location=self.l1.pk,
            instance=self.l1int.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:location_instance_detail",
                    location=self.l1.pk,
                    instance=self.l1int.pk,
                )
                self.response_forbidden()

    def test_normal_workflow(self):
        """
        Ensure details load for authorized user.
        """
        with self.login(username=self.user1):
            self.assertGoodView(
                "fiction_outlines:location_instance_detail",
                location=self.l1.pk,
                instance=self.l1int.pk,
            )
            self.assertInContext("location_instance")
            assert self.l1int == self.get_context("location_instance")


class LocationInstanceCreateTest(FictionOutlineViewTestCase):
    """
    Tests for Location Instance update.
    """

    def test_login_required(self):
        """
        Login is required.
        """
        self.assertLoginRequired(
            "fiction_outlines:location_instance_create", location=self.l1.pk
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user3, self.user2]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:location_instance_create", location=self.l1.pk
                )
                self.response_forbidden()

                before_create = self.l1.locationinstance_set.count()
                self.post(
                    "fiction_outlines:location_instance_create",
                    location=self.l1.pk,
                    data={"outline": self.o2.pk},
                )
                assert (
                    before_create == LocationInstance.objects.filter(location=self.l1).count()
                )

    def test_invalid_post(self):
        """
        Test authorized user but invalid outline selection.
        """
        before_create = self.l1.locationinstance_set.count()
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:location_instance_create",
                location=self.l1.pk,
                data={"outline": self.o3.pk},
            )
            self.response_200()
            form = self.get_context("form")
            assert len(form.errors) == 1
            assert (
                before_create == LocationInstance.objects.filter(location=self.l1).count()
            )
            try:
                with transaction.atomic():
                    with pytest.raises(IntegrityError):
                        self.post(
                            "fiction_outlines:location_instance_create",
                            location=self.l1.pk,
                            data={"outline": self.o2.pk},
                        )
            except IntegrityError:
                pass  # Have to do this otherwise the integrity error breaks the test run.

    def test_valid_post(self):
        before_create = self.l1.locationinstance_set.count()
        o4 = Outline(
            title="Another outline", description="I did a thing!", user=self.user1
        )
        o4.save()
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:location_instance_create", location=self.l1.pk
            )
            self.assertInContext("form")
            self.post(
                "fiction_outlines:location_instance_create",
                location=self.l1.pk,
                data={"outline": o4.pk},
            )
            assert (
                LocationInstance.objects.filter(location=self.l1).count() - before_create == 1
            )
            assert o4.locationinstance_set.count() == 1


class LocationInstanceUpdateTest(FictionOutlineViewTestCase):
    """
    Tests for Location Instance update.
    """

    def test_login_required(self):
        """
        Login is required.
        """
        self.assertLoginRequired(
            "fiction_outlines:location_instance_update",
            location=self.l1.pk,
            instance=self.l1int.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user3, self.user2]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:location_instance_update",
                    location=self.l1.pk,
                    instance=self.l1int.pk,
                )
                self.response_forbidden()

                self.post(
                    "fiction_outlines:location_instance_update",
                    location=self.l1.pk,
                    instance=self.l1int.pk,
                    data={"outline": self.o2.pk},
                )
                assert self.l1int == LocationInstance.objects.get(pk=self.l1int.pk)

    def test_invalid_post(self):
        """
        Test authorized user but invalid outline selection.
        """
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:location_instance_update",
                location=self.l1.pk,
                instance=self.l1int.pk,
                data={"outline": self.o3.pk},
            )
            self.response_200()
            form = self.get_context("form")
            assert len(form.errors) == 1
            assert self.l1int == LocationInstance.objects.get(pk=self.l1int.pk)
            try:
                with transaction.atomic():
                    with pytest.raises(IntegrityError):
                        self.post(
                            "fiction_outlines:location_instance_update",
                            location=self.l1.pk,
                            instance=self.l1int.pk,
                            data={"outline": self.o2.pk},
                        )
            except IntegrityError:
                pass  # Have to do this otherwise the integrity error breaks the test run.

    def test_valid_post(self):
        with self.login(username=self.user1.username):
            o4 = Outline(title="Something new", user=self.user1)
            o4.save()
            self.assertGoodView(
                "fiction_outlines:location_instance_update",
                location=self.l1.pk,
                instance=self.l1int.pk,
            )
            self.assertInContext("form")
            assert self.l1int == self.get_context("location_instance")
            self.post(
                "fiction_outlines:location_instance_update",
                location=self.l1.pk,
                instance=self.l1int.pk,
                data={"outline": o4.pk},
            )
            assert o4 == LocationInstance.objects.get(pk=self.l1int.pk).outline


class ArcListViewTestCase(FictionOutlineViewTestCase):
    """
    Test cases for the arc list view which is filtered by outline.
    """

    def test_login_required(self):
        """
        Assert that you need to be logged in to access this.
        """
        self.assertLoginRequired("fiction_outlines:arc_list", outline=self.o1.pk)
        self.assertLoginRequired("fiction_outlines:arc_list", outline=self.o2.pk)
        self.assertLoginRequired("fiction_outlines:arc_list", outline=self.o3.pk)

    def test_restrict_to_approved_viewer(self):
        """
        Assert that only a user with the proper object permissions can access this list.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:arc_list", outline=self.o1.pk)
            self.get("fiction_outlines:arc_list", outline=self.o1.pk)
            arcs = self.get_context("arc_list")
            assert len(arcs) == Arc.objects.filter(outline=self.o1).count()
            assert self.arc1 in arcs
            assert self.arc2 in arcs
            for arc in arcs:
                assert arc.arcelementnode_set.filter(depth__gt=1).count() == 7
            self.assertGoodView("fiction_outlines:arc_list", outline=self.o2.pk)
            self.get("fiction_outlines:arc_list", outline=self.o2.pk)
            arcs = self.get_context("arc_list")
            assert len(arcs) == Arc.objects.filter(outline=self.o2).count()
            assert self.arc3 in arcs
            assert self.arc4 in arcs
            for arc in arcs:
                assert arc.arcelementnode_set.filter(depth__gt=1).count() == 7
            self.get("fiction_outlines:arc_list", outline=self.o3.pk)
            self.response_forbidden()
        with self.login(username=self.user2.username):
            self.get("fiction_outlines:arc_list", outline=self.o1.pk)
            self.response_forbidden()
            self.get("fiction_outlines:arc_list", outline=self.o2.pk)
            self.response_forbidden()
            self.assertGoodView("fiction_outlines:arc_list", outline=self.o3.pk)
            self.get("fiction_outlines:arc_list", outline=self.o3.pk)
            arcs = self.get_context("arc_list")
            assert len(arcs) == Arc.objects.filter(outline=self.o3).count()
            assert self.arc5 in arcs
            for arc in arcs:
                assert arc.arcelementnode_set.filter(depth__gt=1).count() == 7
        with self.login(username=self.user3.username):
            for outline in [self.o1, self.o2, self.o3]:
                self.get("fiction_outlines:arc_list", outline=outline.pk)
                self.response_forbidden()


class ArcDetailTest(FictionOutlineViewTestCase):
    """
    Test for arc detail view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:arc_detail", outline=self.o1.pk, arc=self.arc1.pk
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:arc_detail", outline=self.o1.pk, arc=self.arc1.pk
                )
                self.response_forbidden()

    def test_normal_workflow(self):
        """
        Ensure an authorized user can access the arc.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:arc_detail", outline=self.o1.pk, arc=self.arc1.pk
            )
            self.assertInContext("arc")
            assert self.arc1 == self.get_context("arc")


class ArcCreateTest(FictionOutlineViewTestCase):
    """
    Test for arc creation.
    """

    def test_login_required(self):
        """
        You must be logged in.
        """
        self.assertLoginRequired("fiction_outlines:arc_create", outline=self.o1.pk)

    def test_object_permissions(self):
        """
        Ensure that you can only create the arc if you can access the outline.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get("fiction_outlines:arc_create", outline=self.o1.pk)
                self.response_forbidden()

                count_of_arcs_outline = Arc.objects.filter(outline=self.o1).count()
                self.post(
                    "fiction_outlines:arc_create",
                    outline=self.o1.pk,
                    data={
                        "name": "Retrieve the missing anaconda",
                        "mace_type": "answer",
                    },
                )
                self.response_forbidden()

                assert (
                    count_of_arcs_outline == Arc.objects.filter(outline=self.o1).count()
                )

    def test_allowed_workflow(self):
        """
        Test authorized user.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView("fiction_outlines:arc_create", outline=self.o1.pk)
            self.assertInContext("form")
            assert self.o1 == Outline.objects.get(pk=self.o1.pk)
            count_of_arcs_outline = Arc.objects.filter(outline=self.o1).count()
            self.post(
                "fiction_outlines:arc_create",
                outline=self.o1.pk,
                data={"name": "Retrieve the missing anaconda", "mace_type": "gabbagoo"},
            )
            self.response_200()
            form = self.get_context("form")
            assert len(form.errors) > 0
            self.post(
                "fiction_outlines:arc_create",
                outline=self.o1.pk,
                data={"name": "Retrieve the missing anaconda", "mace_type": "answer"},
            )
            assert count_of_arcs_outline < Arc.objects.filter(outline=self.o1).count()
            assert (
                "Retrieve the missing anaconda" == Arc.objects.filter(outline=self.o1).latest("created").name
            )


class ArcUpdateTest(FictionOutlineViewTestCase):
    """
    Tests for Arc update view.
    """

    def test_login_required(self):
        self.assertLoginRequired(
            "fiction_outlines:arc_update", outline=self.o1.pk, arc=self.arc1.pk
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:arc_update", outline=self.o1.pk, arc=self.arc1.pk
                )
                self.response_forbidden()

                self.post(
                    "fiction_outlines:arc_update",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    data={"name": "Cha-cha-changes", "mace_type": "event"},
                )
                assert self.arc1.name == Arc.objects.get(pk=self.arc1.pk).name

    def test_normal_workflow(self):
        """
        Test with an authorized user.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:arc_update", outline=self.o1.pk, arc=self.arc1.pk
            )
            self.assertInContext("form")
            assert self.arc1 == self.get_context("arc")
            # Try with an invalid form.
            self.post(
                "fiction_outlines:arc_update",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                data={"name": "Cha-cha-changes", "mace_type": "KABOOM"},
            )
            self.response_200()
            form = self.get_context("form")
            assert len(form.errors) > 0
            assert self.arc1.name == Arc.objects.get(pk=self.arc1.pk).name
            self.post(
                "fiction_outlines:arc_update",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                data={"name": "Cha-cha-changes", "mace_type": "event"},
            )
            assert "Cha-cha-changes" == Arc.objects.get(pk=self.arc1.pk).name


class ArcDeleteTest(FictionOutlineViewTestCase):
    """
    Tests for arc delete view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:arc_delete", outline=self.o1.pk, arc=self.arc1.pk
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access it.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:arc_delete", outline=self.o1.pk, arc=self.arc1.pk
                )
                self.response_forbidden()
                self.post(
                    "fiction_outlines:arc_delete", outline=self.o1.pk, arc=self.arc1.pk
                )
                assert Arc.objects.get(pk=self.arc1.pk)

    def test_normal_workflow(self):
        """
        Test as authorized user.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:arc_delete", outline=self.o1.pk, arc=self.arc1.pk
            )
            assert self.arc1 == self.get_context("arc")
            self.post(
                "fiction_outlines:arc_delete", outline=self.o1.pk, arc=self.arc1.pk
            )
            with pytest.raises(ObjectDoesNotExist):
                Arc.objects.get(pk=self.arc1.pk)


class ArcNodeAbstractTestCase(FictionOutlineViewTestCase):
    """
    Adds additional properties to test.
    """

    def setUp(self):
        super().setUp()
        self.node_to_test = self.arc1.arc_root_node.get_children()[0]
        self.part1 = self.o1.story_tree_root.add_child(
            name="Part 1",
            description="A long time ago in a galaxy far away",
            story_element_type="part",
        )
        self.o1_valid_storynode = self.part1.add_child(
            name="Chapter One",
            story_element_type="chapter",
            description="Our story begins",
        )
        self.o1_invalid_node = self.o2.story_tree_root.add_child(
            name="Chapter One",
            story_element_type="chapter",
            description="A totally different story begins.",
        )


class ArcnodeDetailViewTest(ArcNodeAbstractTestCase):
    """
    Tests for the detail view for an arcnode element.
    """

    def test_login_request(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:arcnode_detail",
            outline=self.o1.pk,
            arc=self.arc1.pk,
            arcnode=self.node_to_test.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:arcnode_detail",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    arcnode=self.node_to_test.pk,
                )
                self.response_forbidden()

    def test_object_owner_access(self):
        """
        Ensure the authorized owner can access the view correctly.
        """
        with self.login(username=self.user1.username):
            anode = ArcElementNode.objects.get(pk=self.node_to_test.pk)
            assert anode
            assert self.user1.has_perm("fiction_outlines.view_arc_node", anode)
            self.assertGoodView(
                "fiction_outlines:arcnode_detail",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
            )
            self.assertInContext("arcnode")
            assert self.node_to_test == self.get_context("arcnode")


class ArcNodeUpdateViewTest(ArcNodeAbstractTestCase):
    """
    Tests for the arc node update view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:arcnode_update",
            outline=self.o1.pk,
            arc=self.arc1.pk,
            arcnode=self.node_to_test.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:arcnode_update",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    arcnode=self.node_to_test.pk,
                )
                self.response_forbidden()

                self.post(
                    "fiction_outlines:arcnode_update",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    arcnode=self.node_to_test.pk,
                    data={
                        "arc_element_type": "mile_hook",
                        "description": "Ha! Pwned!",
                        "story_element_node": self.o1_valid_storynode.pk,
                    },
                )
                assert self.node_to_test == ArcElementNode.objects.get(
                    pk=self.node_to_test.pk
                )

    def test_invalid_submission(self):
        """
        Test invalid data submission from authorized user.
        Examples are:
        - Submit with character from wrong outline
        - Submit with location from wrong outline
        - Submit with storynode from wrong outline.
        """
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:arcnode_update",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                data={
                    "name": "Chapter 1",
                    "description": "Our hero begins their story",
                    "story_element_node": self.o1_valid_storynode.pk,
                    "assoc_characters": (self.c3int.pk, self.c2int.pk),
                    "assoc_locations": (self.l1int.pk),
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert self.node_to_test == ArcElementNode.objects.get(
                pk=self.node_to_test.pk
            )
            self.post(
                "fiction_outlines:arcnode_update",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                data={
                    "arc_element_type": "mile_hook",
                    "description": "Our hero begins their story",
                    "story_element_node": self.o1_valid_storynode.pk,
                    "assoc_characters": (self.c1int.pk, self.c2int.pk),
                    "assoc_locations": (self.l1int2.pk),
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert self.node_to_test == ArcElementNode.objects.get(
                pk=self.node_to_test.pk
            )
            self.post(
                "fiction_outlines:arcnode_update",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                data={
                    "arc_element_type": "mile_hook",
                    "description": "Our hero begins their story",
                    "story_element_node": self.o1_invalid_node.pk,
                    "assoc_characters": (self.c1int.pk, self.c2int.pk),
                    "assoc_locations": (self.l1int.pk),
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert self.node_to_test == ArcElementNode.objects.get(
                pk=self.node_to_test.pk
            )
            self.post(
                "fiction_outlines:arcnode_update",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                data={
                    "arc_element_type": "mile_pt1",
                    "description": "Our hero begins their story",
                    "story_element_node": self.o1_valid_storynode.pk,
                    "assoc_characters": (self.c1int.pk, self.c2int.pk),
                    "assoc_locations": (self.l1int.pk),
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert (
                self.node_to_test.arc_element_type == ArcElementNode.objects.get(pk=self.node_to_test.pk).arc_element_type # noqa
            )

    def test_valid_form_submission(self):
        """
        Test valid form from authorized user.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:arcnode_update",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
            )
            self.assertInContext("form")
            assert self.node_to_test == self.get_context("arcnode")
            self.post(
                "fiction_outlines:arcnode_update",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                data={
                    "arc_element_type": "mile_hook",
                    "description": "Our hero begins their story",
                    "story_element_node": self.o1_valid_storynode.pk,
                    "assoc_characters": (self.c1int.pk, self.c2int.pk),
                    "assoc_locations": (self.l1int.pk),
                },
            )
            new_node = ArcElementNode.objects.get(pk=self.node_to_test.pk)
            assert new_node.story_element_node == self.o1_valid_storynode
            for cint in new_node.assoc_characters.all():
                assert cint in [self.c1int, self.c2int]
                for lint in new_node.assoc_locations.all():
                    assert lint in [self.l1int]


class ArcNodeMoveTest(ArcNodeAbstractTestCase):
    """
    Tests for arcnode move view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:arcnode_move",
            outline=self.o1.pk,
            arc=self.arc1.pk,
            arcnode=self.node_to_test.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access or move the node.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:arcnode_move",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    arcnode=self.node_to_test.pk,
                )
                self.response_forbidden()
                self.post(
                    "fiction_outlines:arcnode_move",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    arcnode=self.node_to_test.pk,
                    data={
                        "_ref_node_id": self.node_to_test.get_next_sibling().pk,
                        "_position": "right",
                    },
                )
                self.response_forbidden()
                assert (
                    self.node_to_test.path == ArcElementNode.objects.get(pk=self.node_to_test.pk).path
                )

    def test_valid_move(self):
        """
        Test a valid move from an authorized user.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:arcnode_move",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                test_query_count=160,
            )
            self.assertInContext("form")
            next_sibling = self.node_to_test.get_next_sibling()
            print("Found next sibling of %s " % next_sibling)
            self.post(
                "fiction_outlines:arcnode_move",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                data={"_ref_node_id": next_sibling.pk, "_position": "right"},
            )
            print(self.last_response.content)
            self.response_302()
            assert (
                self.node_to_test.path != ArcElementNode.objects.get(pk=self.node_to_test.pk).path
            )

    def test_invalid_move(self):
        """
        Test that an invalid move is prevented even by authorized users.
        """
        with self.login(username=self.user1.username):
            arc2 = self.o1.create_arc(
                name="Totally different arc", mace_type="character"
            )
            invalid_target_node = arc2.arc_root_node.get_children()[2]
            self.post(
                "fiction_outlines:arcnode_move",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                data={"_ref_node_id": invalid_target_node.pk, "_position": "right"},
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert (
                self.node_to_test.path == ArcElementNode.objects.get(pk=self.node_to_test.pk).path
            )
            new_beat = self.node_to_test.add_child(
                arc_element_type="beat", description="I am a beat"
            )
            # Verify that we gracefully handle trying to move to a descendant node, which is not OK.
            self.post(
                "fiction_outlines:arcnode_move",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                data={"_ref_node_id": new_beat.pk, "_position": "right"},
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert (
                self.node_to_test.path == ArcElementNode.objects.get(pk=self.node_to_test.pk).path
            )


class ArcNodeDeleteTest(ArcNodeAbstractTestCase):
    """
    Tests for arcnode delete view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:arcnode_delete",
            outline=self.o1.pk,
            arc=self.arc1.pk,
            arcnode=self.node_to_test.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access or delete object.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:arcnode_delete",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    arcnode=self.node_to_test.pk,
                )
                self.response_forbidden()
                self.post(
                    "fiction_outlines:arcnode_delete",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    arcnode=self.node_to_test.pk,
                )
                self.response_forbidden()
                assert ArcElementNode.objects.get(pk=self.node_to_test.pk)

    def test_normal_workflow(self):
        """
        Test with an authorized user.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:arcnode_delete",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
            )
            assert self.node_to_test == self.get_context("arcnode")
            self.assertResponseContains(
                "You cannot delete the hook of an arc.", html=False
            )
            self.post(
                "fiction_outlines:arcnode_delete",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
            )
            # You can't delete the hook or resolution.
            self.response_200()
            assert ArcElementNode.objects.get(pk=self.node_to_test.pk)
            # Check against the resolution
            reso = self.arc1.arc_root_node.get_children()[6]
            assert reso.arc_element_type == "mile_reso"
            self.assertGoodView(
                "fiction_outlines:arcnode_delete",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=reso.pk,
            )
            self.assertResponseContains(
                "You cannot delete the resolution of an arc.", html=False
            )
            self.post(
                "fiction_outlines:arcnode_delete",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=reso.pk,
            )
            self.response_200()
            assert ArcElementNode.objects.get(pk=reso.pk)
            pt1 = self.arc1.arc_root_node.get_children()[1]
            assert pt1.arc_element_type == "mile_pt1"
            self.assertGoodView(
                "fiction_outlines:arcnode_delete",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=pt1.pk,
            )
            self.assertResponseNotContains("You cannot delete the", html=False)
            self.post(
                "fiction_outlines:arcnode_delete",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=pt1.pk,
            )
            with pytest.raises(ObjectDoesNotExist):
                ArcElementNode.objects.get(pk=pt1.pk)


class ArcNodeCreateTest(ArcNodeAbstractTestCase):
    """
    Tests for the ArcNode create view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:arcnode_create",
            outline=self.o1.pk,
            arc=self.arc1.pk,
            arcnode=self.node_to_test.pk,
            pos="addchild",
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot add to the arc tree.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:arcnode_create",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    arcnode=self.node_to_test.pk,
                    pos="addchild",
                )
                self.response_forbidden()

                self.post(
                    "fiction_outlines:arcnode_create",
                    outline=self.o1.pk,
                    arc=self.arc1.pk,
                    arcnode=self.node_to_test.pk,
                    pos="addchild",
                    data={
                        "arc_element_type": "beat",
                        "description": "This beat should not be here",
                    },
                )
                self.response_forbidden()
                self.node_to_test.refresh_from_db()
                assert not self.node_to_test.get_children()

    def test_authorized_creations(self):
        """
        Test that an authorized user can create nodes.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:arcnode_create",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                pos="addchild",
            )
            self.assertGoodView(
                "fiction_outlines:arcnode_create",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                pos="left",
            )
            self.assertInContext("form")
            self.post(
                "fiction_outlines:arcnode_create",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                pos="addchild",
                data={
                    "arc_element_type": "beat",
                    "description": "This beat should be here",
                },
            )
            self.node_to_test.refresh_from_db()
            assert len(self.node_to_test.get_children()) > 0
            self.post(
                "fiction_outlines:arcnode_create",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                pos="right",
                data={
                    "arc_element_type": "beat",
                    "description": "This beat should be here",
                },
            )
            self.node_to_test.refresh_from_db()
            assert (
                self.node_to_test.get_next_sibling().description
                == "This beat should be here"
            )
            self.post(
                "fiction_outlines:arcnode_create",
                outline=self.o1.pk,
                arc=self.arc1.pk,
                arcnode=self.node_to_test.pk,
                pos="right",
                data={
                    "arc_element_type": "mile_pt1",
                    "description": "This plot turn is a duplicate milestone and should be rejected.",
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            self.node_to_test.refresh_from_db()
            assert self.node_to_test.get_next_sibling().arc_element_type == "beat"


class StoryNodeDetailTest(ArcNodeAbstractTestCase):
    """
    Tests for the detail view of a story element node.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:storynode_detail",
            outline=self.o1.pk,
            storynode=self.o1_valid_storynode.pk,
        )

    def test_object_permissions(self):
        """
        Ensure only authorized users can access the object.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:storynode_detail",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                )
                self.response_forbidden()

    def test_normal_workflow(self):
        """
        Test that an authorized user can access the data.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:storynode_detail",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
            )
            assert self.o1_valid_storynode == self.get_context("storynode")


class StoryNodeCreateTest(ArcNodeAbstractTestCase):
    """
    Tests for StoryNode creation view.
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:storynode_create",
            outline=self.o1.pk,
            storynode=self.o1_valid_storynode.pk,
            pos="addchild",
        )

    def test_object_permissions(self):
        """
        Ensure that unauthorized users cannot create new nodes in the outline.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:storynode_create",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                    pos="addchild",
                )
                self.response_forbidden()
                self.post(
                    "fiction_outlines:storynode_create",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                    pos="addchild",
                    data={
                        "story_element_type": "ss",
                        "name": "unexpected party",
                        "description": "In this scene, our hero must play host to sloths.",
                    },
                )
                self.response_forbidden()
                self.o1_valid_storynode.refresh_from_db()
                assert not self.o1_valid_storynode.get_children()
                self.post(
                    "fiction_outlines:storynode_create",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                    pos="right",
                )
                self.response_forbidden()
                self.o1_valid_storynode.refresh_from_db()
                assert not self.o1_valid_storynode.get_next_sibling()

    def test_authorized_user(self):
        """
        Ensure that an authorized user can create as needed.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:storynode_create",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                pos="addchild",
            )
            self.assertGoodView(
                "fiction_outlines:storynode_create",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                pos="right",
            )
            self.assertInContext("form")
            self.post(
                "fiction_outlines:storynode_create",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                pos="addchild",
                data={
                    "story_element_type": "part",
                    "name": "bad part",
                    "description": "In this scene, our hero must play host to sloths.",
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            self.o1_valid_storynode.refresh_from_db()
            assert not self.o1_valid_storynode.get_children()
            self.post(
                "fiction_outlines:storynode_create",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                pos="addchild",
                data={
                    "story_element_type": "ss",
                    "name": "unexpected party",
                    "description": "In this scene, our hero must play host to sloths.",
                },
            )
            self.o1_valid_storynode.refresh_from_db()
            assert len(self.o1_valid_storynode.get_children()) == 1
            self.post(
                "fiction_outlines:storynode_create",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                pos="right",
                data={
                    "story_element_type": "chapter",
                    "name": "Cleaning up",
                    "description": "In this scene, our hero must pick up sloth feces.",
                },
            )
            self.o1_valid_storynode.refresh_from_db()
            assert self.o1_valid_storynode.get_next_sibling().name == "Cleaning up"


class StoryNodeUpdateTest(ArcNodeAbstractTestCase):
    """
    Test for story node update view
    """

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:storynode_update",
            outline=self.o1.pk,
            storynode=self.o1_valid_storynode.pk,
        )

    def test_object_permissions(self):
        """
        Ensure that an unauthorized user cannot access or edit the object even if they do everything else right.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:storynode_update",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                )
                self.response_forbidden()
                self.post(
                    "fiction_outlines:storynode_update",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                    data={
                        "name": "Chapter 1",
                        "description": "Updating the description",
                        "story_element_type": "chapter",
                    },
                )
                self.response_forbidden()
                assert self.o1_valid_storynode == StoryElementNode.objects.get(
                    pk=self.o1_valid_storynode.pk
                )

    def test_with_authorized_user(self):
        """
        Test an invalid form submission from an authorized user.
        """
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:storynode_update",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                data={
                    "name": "Chapter 1",
                    "description": "Updating the description",
                    "story_element_type": "chapter",
                    "assoc_characters": (self.c3int.pk),
                    "assoc_locations": (self.l1int.pk),
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert self.o1_valid_storynode == StoryElementNode.objects.get(
                pk=self.o1_valid_storynode.pk
            )
            self.post(
                "fiction_outlines:storynode_update",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                data={
                    "name": "Chapter 1",
                    "description": "Updating the description",
                    "story_element_type": "chapter",
                    "assoc_characters": (self.c1int.pk),
                    "assoc_locations": (self.l1int2.pk),
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert self.o1_valid_storynode == StoryElementNode.objects.get(
                pk=self.o1_valid_storynode.pk
            )
            # You can't make a part descend from another part.
            self.post(
                "fiction_outlines:storynode_update",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                data={
                    "name": "Chapter 1",
                    "description": "Updating the description",
                    "story_element_type": "part",
                    "assoc_characters": (self.c1int.pk),
                    "assoc_locations": (self.l1int.pk),
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert self.o1_valid_storynode == StoryElementNode.objects.get(
                pk=self.o1_valid_storynode.pk
            )
            # Now a valid change
            self.post(
                "fiction_outlines:storynode_update",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                data={
                    "name": "Chapter 1",
                    "description": "Updating the description",
                    "story_element_type": "chapter",
                    "assoc_characters": (self.c1int.pk),
                    "assoc_locations": (self.l1int.pk),
                },
            )
            updated_version = StoryElementNode.objects.get(
                pk=self.o1_valid_storynode.pk
            )
            assert updated_version.description == "Updating the description"
            for cint in updated_version.assoc_characters.all():
                assert cint in [self.c1int]
            for lint in updated_version.assoc_locations.all():
                assert lint in [self.l1int]


class StoryNodeMoveTest(ArcNodeAbstractTestCase):
    """
    Tests for storynode move view.
    """

    def setUp(self):
        super().setUp()
        self.o1_scene1 = self.o1_valid_storynode.add_child(
            story_element_type="ss",
            name="Staring in a mirror",
            description="describe the protagonist",
        )
        self.o1_valid_storynode.refresh_from_db()
        self.o1_scene2 = self.o1_valid_storynode.add_child(
            story_element_type="ss",
            name="walk and talk",
            description="copy and paste, find and replace.",
        )
        self.o1_valid_storynode.refresh_from_db()
        self.o1_chap2 = self.part1.add_child(
            story_element_type="chapter",
            name="chapter2",
            description="I have no idea what I'm doing",
        )
        self.part1.refresh_from_db()

    def test_login_required(self):
        """
        You have to be logged in.
        """
        self.assertLoginRequired(
            "fiction_outlines:storynode_move",
            outline=self.o1.pk,
            storynode=self.o1_valid_storynode.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access or move the node.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:storynode_move",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                )
                self.response_forbidden()
                self.post(
                    "fiction_outlines:storynode_move",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                    data={"_ref_node_id": self.o1_chap2.pk, "_position": "right"},
                )
                self.response_forbidden()
                assert (
                    self.o1_valid_storynode.path
                    == StoryElementNode.objects.get(pk=self.o1_valid_storynode.pk).path
                )

    def test_valid_move(self):
        """
        Test a valid move from an authorized user.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:storynode_move",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
            )
            self.assertInContext("form")
            next_sibling = self.o1_valid_storynode.get_next_sibling()
            print("Found next sibling of %s " % next_sibling)
            self.post(
                "fiction_outlines:storynode_move",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                data={"_ref_node_id": next_sibling.pk, "_position": "right"},
            )
            print(self.last_response.content)
            self.response_302()
            assert (
                self.o1_valid_storynode.path
                != StoryElementNode.objects.get(pk=self.o1_valid_storynode.pk).path
            )

    def test_invalid_move(self):
        """
        Test that an invalid move is prevented even by authorized users.
        """
        with self.login(username=self.user1.username):
            self.post(
                "fiction_outlines:storynode_move",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                data={
                    "_ref_node_id": self.o1_valid_storynode.get_root().pk,
                    "_position": "right",
                },
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert (
                self.o1_valid_storynode.path
                == StoryElementNode.objects.get(pk=self.o1_valid_storynode.pk).path
            )
            # Verify that we gracefully handle trying to move to a descendant node, which is not OK.
            self.post(
                "fiction_outlines:storynode_move",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                data={"_ref_node_id": self.o1_scene1.pk, "_position": "right"},
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert (
                self.o1_valid_storynode.path
                == StoryElementNode.objects.get(pk=self.o1_valid_storynode.pk).path
            )
            # Ensure you can't violate the rules of outline structure.
            self.post(
                "fiction_outlines:storynode_move",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
                data={"_ref_node_id": self.o1_chap2.pk, "_postion": "first-child"},
            )
            self.response_200()
            assert len(self.get_context("form").errors) > 0
            assert (
                self.o1_valid_storynode.path
                == StoryElementNode.objects.get(pk=self.o1_valid_storynode.pk).path
            )


class StoryNodeDeleteTest(ArcNodeAbstractTestCase):
    """
    Tests for the story node deletion view.
    """

    def test_login_required(self):
        self.assertLoginRequired(
            "fiction_outlines:storynode_delete",
            outline=self.o1.pk,
            storynode=self.o1_valid_storynode.pk,
        )

    def test_object_permissions(self):
        """
        Ensure unauthorized users cannot access or delete.
        """
        for user in [self.user2, self.user3]:
            with self.login(username=user.username):
                self.get(
                    "fiction_outlines:storynode_delete",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                )
                self.response_forbidden()
                self.post(
                    "fiction_outlines:storynode_delete",
                    outline=self.o1.pk,
                    storynode=self.o1_valid_storynode.pk,
                )
                self.response_forbidden()
                assert StoryElementNode.objects.get(pk=self.o1_valid_storynode.pk)

    def test_normal_workflow(self):
        """
        Test that an authorized user can access the view and delete.
        """
        with self.login(username=self.user1.username):
            self.assertGoodView(
                "fiction_outlines:storynode_delete",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
            )
            assert self.get_context("storynode") == self.o1_valid_storynode
            self.post(
                "fiction_outlines:storynode_delete",
                outline=self.o1.pk,
                storynode=self.o1_valid_storynode.pk,
            )
            with pytest.raises(ObjectDoesNotExist):
                StoryElementNode.objects.get(pk=self.o1_valid_storynode.pk)
