import io
import json
import re
import django
import xml.etree.ElementTree as ET
from test_plus import TestCase
from fiction_outlines.models import Outline, StoryElementNode, Series
from fiction_outlines.models import Character, CharacterInstance, Location, LocationInstance


class AbstractExportTestCase(TestCase):
    '''
    Abstract test case so that we can reinitializer our variables.
    '''

    def setUp(self):
        self.user1 = self.make_user('u1')
        self.user2 = self.make_user('u2')
        self.user3 = self.make_user('u3')
        self.bad_users = [self.user2, self.user3]
        self.s1 = Series(title='Urban Fantasy Trilogy', user=self.user1)
        self.s1.save()
        self.o1 = Outline(title='Dark Embrace', description='Vampire romance', series=self.s1, user=self.user1)
        self.o1.save()
        self.o1.tags.add('sexy')
        self.o1.tags.add('vampire')
        self.c1 = Character(name='John', user=self.user1)
        self.c1.save()
        self.c1int = CharacterInstance(character=self.c1, outline=self.o1)
        self.c1int.save()
        self.l1 = Location(name='Bar', user=self.user1)
        self.l1.save()
        self.lint = LocationInstance(location=self.l1, outline=self.o1)
        self.lint.save()
        self.arc1 = self.o1.create_arc(mace_type='event', name='dragon invasion')
        self.arc2 = self.o1.create_arc(mace_type='character', name='coming of age')

        def get_node(node_id): return StoryElementNode.objects.get(pk=node_id)
        story_root = self.o1.story_tree_root
        self.part1 = story_root.add_child(name='Part 1', story_element_type='part')
        self.part2 = get_node(story_root.pk).add_child(name='Part 2', story_element_type='part')
        self.part3 = get_node(story_root.pk).add_child(name='Part 3', story_element_type='part')
        self.chap1 = self.part1.add_child(name='Chapter 1', story_element_type='chapter')
        self.chap2 = get_node(self.part1.pk).add_child(name='Chapter 2', story_element_type='chapter')
        self.chap3 = get_node(self.part2.pk).add_child(name='Chapter 3', story_element_type='chapter')
        self.chap4 = get_node(self.part2.pk).add_child(name='Chapter 4', story_element_type='chapter')
        self.chap5 = get_node(self.part3.pk).add_child(name='Chapter 5', story_element_type='chapter')
        self.epi = get_node(self.part3.pk).add_child(name='Epilogue', story_element_type='chapter')
        self.epi.description = """Our hero tries to come to terms with how his adventure has changed himself and others."""  # noqa: E501
        self.epi.save()
        self.scene1 = get_node(self.chap1.pk).add_child(name='A dark night', description='A rainy night in the city',
                                                        story_element_type='ss')
        self.scene2 = get_node(self.chap1.pk).add_child(name='A chance meetings', description='Our hero encounters a strange woman and is intrigued.',  # noqa: E501
                                                        story_element_type='ss')  # noqa: E501
        self.scene3 = get_node(self.chap2.pk).add_child(name='Work together?', description="The two of them are forced to work together to solve a mystery.",  # noqa: E501
                                                        story_element_type='ss')  # noqa: E501
        self.scene7 = get_node(self.chap4.pk).add_child(name='Showdown', description='A big battle with the villain!',
                                                        story_element_type='ss')

    def response_forbidden(self):
        if django.VERSION < (2, 1):
            return self.response_302()
        return self.response_403()


class OPMLExportTestCase(AbstractExportTestCase):
    '''
    Test that the OPML export works as expected.
    '''

    def setUp(self):
        super().setUp()
        self.view_string = 'fiction_outlines:outline_export'
        self.url_kwargs = {'outline': self.o1.pk, 'format': 'opml'}

    def test_login_required(self):
        '''
        You have to be logged in.
        '''
        self.assertLoginRequired(self.view_string, **self.url_kwargs)

    def test_object_permissions(self):
        '''
        Ensure unauthorized users cannot access the object.
        '''
        for user in self.bad_users:
            with self.login(username=user.username):
                self.get(self.view_string, **self.url_kwargs)
                self.response_forbidden()

    def test_valid_user(self):
        '''
        Check with an authorized user.
        '''
        with self.login(username=self.user1.username):
            self.assertGoodView(self.view_string, **self.url_kwargs)
            assert self.last_response.get('Content-Disposition') == 'attachment; filename="dark-embrace.opml"'
            assert self.get_context('outline') == self.o1
            print(self.last_response.content)
            try:
                f = io.BytesIO(self.last_response.content)
                ET.ElementTree(file=f)
            except ET.ParseError as PE:
                assert not str(PE)  # Failing the test a bit more gracefully.


class JSONExportTestCase(AbstractExportTestCase):
    '''
    Tests for exporting an outline as JSON.
    '''

    def setUp(self):
        super().setUp()
        self.view_string = 'fiction_outlines:outline_export'
        self.url_kwargs = {'outline': self.o1.pk, 'format': 'json'}

    def test_login_required(self):
        '''
        You have to be logged in.
        '''
        self.assertLoginRequired(self.view_string, **self.url_kwargs)

    def test_object_permissions(self):
        '''
        Ensure that unauthorized users cannot access the object.
        '''
        for user in self.bad_users:
            with self.login(username=user.username):
                self.get(self.view_string, **self.url_kwargs)
                self.response_forbidden()

    def test_authorized_user(self):
        '''
        Test the JSON response itself.
        '''
        with self.login(username=self.user1.username):
            self.get(self.view_string, **self.url_kwargs)
            assert self.last_response.get('Content-Disposition') == 'attachment; filename="dark-embrace.json"'
            f = io.BytesIO(self.last_response.content)
            data = json.load(f)
            assert data['title']  # Verifiy the response is JSON.
            assert len(data['series']['tags']) == 0
            assert len(data['tags']) == 2
            assert len(data['characters']) == 1
            assert len(data['locations']) == 1
            assert len(data['arcs']) == 2
            assert len(data['arcs'][0]['nodes']) > 0
            assert len(data['story_tree']) > 0


class MDExportTest(AbstractExportTestCase):
    '''
    Tests for exporting outline as markdown.
    '''

    def setUp(self):
        super().setUp()
        self.view_string = 'fiction_outlines:outline_export'
        self.url_kwargs = {'outline': self.o1.pk, 'format': 'md'}

    def test_login_required(self):
        '''
        You have to be logged in.
        '''
        self.assertLoginRequired(self.view_string, **self.url_kwargs)

    def test_object_permissions(self):
        '''
        Ensure it can't be accessed by an unauthorized user.
        '''
        for user in self.bad_users:
            with self.login(username=user.username):
                self.get(self.view_string, **self.url_kwargs)
                self.response_forbidden()

    def test_authorized_user(self):
        '''
        Test that the actual export is generated correctly.
        '''
        with self.login(username=self.user1.username):
            self.get(self.view_string, **self.url_kwargs)
            self.response_200()
            assert self.last_response.get('Content-Disposition') == 'attachment; filename="dark-embrace.md"'
            f = io.BytesIO(self.last_response.content)
            mdstring = f.read().decode('utf-8')
            scene_breaks = re.compile(r'^----$', flags=re.MULTILINE)
            title_finder = re.compile(r'^# ', flags=re.MULTILINE)
            book_finder = re.compile(r'^## ', flags=re.MULTILINE)
            act_finder = re.compile(r'^### ', flags=re.MULTILINE)
            part_finder = re.compile(r'^#### ', flags=re.MULTILINE)
            chapter_finder = re.compile(r'^##### ', flags=re.MULTILINE)
            assert len(scene_breaks.findall(mdstring)) == 4
            assert len(title_finder.findall(mdstring)) == 1
            assert len(book_finder.findall(mdstring)) == 0
            assert len(act_finder.findall(mdstring)) == 0
            assert len(part_finder.findall(mdstring)) == 3
            assert len(chapter_finder.findall(mdstring)) == 6


class TestBadFormat(AbstractExportTestCase):
    '''
    Tests for invalid format types.
    '''

    def setUp(self):
        super().setUp()
        self.view_string = 'fiction_outlines:outline_export'
        self.url_kwargs = {'outline': self.o1.pk}

    def test_not_implemented(self):
        '''
        Send a series of formats and ensure they all raise exceptions.
        '''
        for format in ['xlsx', 'textbundle', 'html', 'xml']:
            with self.login(username=self.user1.username):
                print("Testing format {}".format(format))
                self.url_kwargs['format'] = format
                self.get(self.view_string, **self.url_kwargs)
                self.response_404()
