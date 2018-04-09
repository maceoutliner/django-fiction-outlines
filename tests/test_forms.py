import pytest
from test_plus import TestCase
from fiction_outlines.models import Series, Outline, Character, CharacterInstance
from fiction_outlines.models import Location, LocationInstance
from fiction_outlines.forms import OutlineMoveNodeForm, OutlineForm, CharacterForm, LocationForm
from fiction_outlines.forms import CharacterInstanceForm, LocationInstanceForm
from fiction_outlines.forms import ArcNodeForm, StoryNodeForm


class AbstractFormTest(TestCase):
    '''
    Initialized variables for Form tests.
    '''

    def setUp(self):
        self.user1 = self.make_user('u1')
        self.user2 = self.make_user('u2')
        self.series1 = Series(title='Hi there', description='Time to die', user=self.user1)
        self.series1.save()
        self.series2 = Series(title="Saga", description='So epid', user=self.user2)
        self.series2.save()
        self.c1 = Character(name='John Doe', user=self.user1)
        self.c1.save()
        self.o1 = Outline(title="opus", user=self.user1, series=self.series1)
        self.o1.save()
        self.l1 = Location(name='spooky house', user=self.user1)
        self.l1.save()
        self.c1int = CharacterInstance(character=self.c1, outline=self.o1)
        self.c1int.save()
        self.l1int = LocationInstance(location=self.l1, outline=self.o1)
        self.l1int.save()
        self.arc1 = self.o1.create_arc(name='coming of age', mace_type='character')


class OutlineMoveNodeTest(AbstractFormTest):
    '''
    Tests for Outline move node form.
    '''

    def test_form_without_root(self):
        with pytest.raises(KeyError):
            form = OutlineMoveNodeForm()  # noqa


class OutlineFormTest(AbstractFormTest):
    '''
    Test for outline form instantiation.
    '''

    def test_form_without_user(self):
        with pytest.raises(KeyError):
            form = OutlineForm()  # noqa


class CharacterFormTest(AbstractFormTest):
    '''
    Test for character form instantiation
    '''

    def test_form_without_user(self):
        with pytest.raises(KeyError):
            form = CharacterForm()  # noqa


class LocationFormTest(AbstractFormTest):
    '''
    Test location form instantiation.
    '''

    def test_form_without_user(self):
        with pytest.raises(KeyError):
            form = LocationForm()  # noqa


class CharacterInstanceFormTest(AbstractFormTest):
    '''
    Test character instance form instantiation.
    '''

    def test_form_without_character(self):
        with pytest.raises(KeyError):
            form = CharacterInstanceForm()  # noqa


class LocationInstanceFormTest(AbstractFormTest):
    '''
    Test location instance form instantiation.
    '''

    def test_form_without_location(self):
        with pytest.raises(KeyError):
            form = LocationInstanceForm()  # noqa


class ArcNodeFormTest(AbstractFormTest):
    '''
    Test arc node form instantiation.
    '''

    def test_form_without_arc(self):
        with pytest.raises(KeyError):
            form = ArcNodeForm()  # noqa


class StoryNodeFormTest(AbstractFormTest):
    '''
    Test story node form instantiation.
    '''

    def test_form_without_outline(self):
        with pytest.raises(KeyError):
            form = StoryNodeForm()  # noqa
