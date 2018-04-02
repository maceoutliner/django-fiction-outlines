'''
Tests for Outline models
'''
import pytest
from test_plus.test import TestCase
from django.db import transaction
from django.db.utils import IntegrityError
from django.forms.models import model_to_dict
from fiction_outlines.models import Arc, Character, CharacterInstance, Location, LocationInstance, ArcIntegrityError
from fiction_outlines.models import ArcElementNode, Outline, StoryElementNode, ARC_NODE_ELEMENT_DEFINITIONS


# Create your tests here.
class ArcModelTest(TestCase):
    '''
    Performs basic tests to ensure that Outlines are not duplicated,
    cannot be seen by someone who doesn't own it, etc.
    '''

    def setUp(self):
        '''
        Create users and base outlines for tests
        '''
        self.user1 = self.make_user('u1')
        self.user2 = self.make_user('u2')
        self.ms1 = Outline(
            title="Monkeys are here",
            description="A sample outline",
            user=self.user1
        )
        self.ms2 = Outline(title="A wild rabbit", description="Let's make stew", user=self.user2)
        self.ms1.save()
        self.ms2.save()
        self.char1 = Character(name="John Doe", user=self.user1)
        self.char1.save()
        self.char2 = Character(name='Jane Smith', user=self.user2)
        self.char2.save()
        self.loc1 = Location(name='Work', user=self.user1)
        self.loc1.save()
        self.loc2 = Location(name='Home', user=self.user2)
        self.loc2.save()
        self.char1_int = CharacterInstance(character=self.char1, outline=self.ms1)
        self.char1_int.save()
        self.char2_int = CharacterInstance(character=self.char2, outline=self.ms2)
        self.char2_int.save()
        self.char3 = Character(name="The shadow", user=self.user2)
        self.char3.save()
        self.char3_int = CharacterInstance(character=self.char3, outline=self.ms2)
        self.char3_int.save()
        self.loc1_int = LocationInstance(location=self.loc1, outline=self.ms1)
        self.loc1_int.save()
        self.loc2_int = LocationInstance(location=self.loc2, outline=self.ms2)
        self.loc2_int.save()
        self.loc3 = Location(name='Haunted Grocery', user=self.user2)
        self.loc3.save()
        self.loc3_int = LocationInstance(location=self.loc3, outline=self.ms2)
        self.loc3_int.save()

    def test_arc_initial_tree_created(self):
        '''
        Ensure that creating an Arc also creates the root element of the tree.
        We will verify the validity of the tree in a later test.
        '''
        arc_sample = self.ms1.create_arc(mace_type='event', name='I ate something gross')
        assert isinstance(arc_sample, Arc)
        assert isinstance(arc_sample.arc_root_node, ArcElementNode)
        assert arc_sample.arc_root_node.is_root()
        assert arc_sample.outline == self.ms1
        assert arc_sample.arc_root_node.get_children().count() == 7
        last_seq = 0
        for node in arc_sample.arc_root_node.get_children():
            assert ARC_NODE_ELEMENT_DEFINITIONS[node.arc_element_type]['milestone']
            current_seq = ARC_NODE_ELEMENT_DEFINITIONS[node.arc_element_type]['milestone_seq']
            assert current_seq > last_seq
            last_seq = current_seq
        with pytest.raises(ArcIntegrityError):
            arc_sample.generate_template_arc_tree()

    def test_arcelement_headline_generated(self):
        '''
        Ensure a headline is generated appropriately.
        '''
        arc_sample = self.ms1.create_arc(mace_type='event', name='I ate something gross')
        arc_root = arc_sample.arc_root_node
        arc_hook = arc_root.get_children().get(arc_element_type='mile_hook')
        arc_hook.description = "This is my hook. There are many like it but this one is mine. I do wonder when the ghosts will come for all of us."  # noqa: E501
        arc_hook.save()
        assert arc_hook.headline == "This is my hook. There are many like it but this one is mine. I do wonder when the ghosts ..."  # noqa: E501
        big_word_headline = '''superexpealodcious mokeyjkdsjfkdljdslkjsdjdljfd djklsdjdfjdsjsljfkdjsdsjsdljdkjflsdkjffsdf dfdadfdasfdsfsadd superexpealodcious mokeyjkdsjfkdljdslkjsdjdljfd djklsdjdfjdsjsljfkdjsdsjsdljdkjflsdkjffsdf dfdadfdasfdsfsadd superexpealodcious mokeyjkdsjfkdljdslkjsdjdljfd djklsdjdfjdsjsljfkdjsdsjsdljdkjflsdkjffsdf dfdadfdasfdsfsad'''  # noqa: E501
        expected_result = '''superexpealodcious mokeyjkdsjfkdljdslkjsdjdljfd djklsdjdfjdsjsljfkdjsdsjsdljdkjflsdkjffsdf dfdadfdasfdsfsadd superexpealodcious mokeyjkdsjfkdljdslkjsdjdljfd djklsdjdfjdsjsljfkdjsdsjsdljdkjflsdkjffsdf dfdadfdasfdsfsadd superexpealodcious mokeyjkdsj...'''  # noqa: E501
        arc_hook.description = big_word_headline
        arc_hook.save()
        assert arc_hook.headline == expected_result
        easy_headline = '''I ate some clams.

        They were yummy.'''
        arc_hook.description = easy_headline
        arc_hook.save()
        assert arc_hook.headline == "I ate some clams."

    def test_duplicate_milestones_blocked(self):
        '''
        Ensures that you can't add two of the same milestone type to an arc.
        '''
        arc_test = self.ms1.create_arc(mace_type='event', name='sloppy arc')
        arc_root = arc_test.arc_root_node
        with pytest.raises(ArcIntegrityError):
            arc_root.add_child(arc_element_type='mile_pt1', description='The plot thickens')
        nodes = arc_root.get_descendants()
        for node in nodes:
            pos = 'right'
            if node.arc_element_type == 'mile_reso':
                pos = 'left'
            with pytest.raises(ArcIntegrityError):
                node.add_sibling(pos=pos, arc_element_type=node.arc_element_type, description='naughty naughty')

    def test_hook_reso_never_delete(self):
        '''
        Ensure that a user can never delete the hook and resolution of the arc unless they delete the whole arc.
        TODO: Not sure how to do this.
        '''
        pass

    def test_arc_validation(self):
        '''
        Verifies that if the tree of an arc checks correctly validate.
        '''
        def get(node_id): return ArcElementNode.objects.get(pk=node_id)
        arc_sample = self.ms1.create_arc(mace_type='event', name='I ate something gross')
        assert arc_sample.current_errors == []
        arc_errors = arc_sample.fetch_arc_errors()
        assert arc_errors == []  # Default template should contain zero errors.
        # For readability's sake, let's extract all the milestones into named
        # python objects instead of positionals.
        hook = arc_sample.arc_root_node.get_first_child()
        print("Hook: %s" % hook.pk)
        pt1 = hook.get_next_sibling()
        print('PT1: %s' % pt1.pk)
        pinch1 = pt1.get_next_sibling()
        print('pinch1: %s' % pinch1.pk)
        midp = pinch1.get_next_sibling()
        print('midp: %s' % midp.pk)
        pinch2 = midp.get_next_sibling()
        print('pinch2: %s' % pinch2.pk)
        pt2 = pinch2.get_next_sibling()
        print('pt2: %s' % pt2.pk)
        reso = arc_sample.arc_root_node.get_last_child()
        print('reso: %s' % reso.pk)
        # The tree currently looks like this:
        #             Root
        # Hook PT1 Pinch1 Midp pinch2 pt2 reso
        print(arc_sample.arc_root_node.dump_bulk())
        # Try moving the hook just before the resolution.
        get(hook.pk).move(reso, 'left')
        # The tree currently looks like this.
        #             Root
        # PT1 Pinch1 Midp Pinch2 pt2 hook reso
        # This should violate both milestone sequence and hook placement.
        assert len(arc_sample.fetch_arc_errors()) == 2
        # Ensure the validation catches the new errors.
        assert arc_sample.current_errors == []  # Still a cached result
        arc_sample.refresh_from_db()
        assert len(arc_sample.current_errors) == 2  # refreshed from db found the new errors.

        def error_check(label, error_list):
            if label in set().union(*(d.keys() for d in error_list)):
                return True
            else:
                return False
        assert error_check('hook_error', arc_sample.current_errors)
        assert error_check('mseq_error', arc_sample.current_errors)
        # Try moving the resolution just after the plot turn 1
        get(reso.pk).move(get(pt1.pk), 'right')
        # The tree currently looks like this.
        #             Root
        # PT1 Reso Pinch1 Midp Pinch2 pt2 hook
        # This violates milestone sequence, hook placement, and resolution placement.
        error_list = arc_sample.fetch_arc_errors()
        assert len(error_list) == 3
        assert error_check('hook_error', error_list)
        assert error_check('mseq_error', error_list)
        assert error_check('reso_error', error_list)
        # Try moving the plot turn 2 underneath the pinch 2.
        get(pt2.pk).move(get(pinch2.pk), 'first-child')
        # The tree currently looks like this.
        #             Root
        # PT1 Reso Pinch1 Midp Pinch2 Hook
        #                      pt2
        # This violates milestone sequence, Hook placement, resolution placement,
        # and generation rules as milestones are only allowed to have
        # the root as their parent.
        error_list = arc_sample.fetch_arc_errors()
        assert len(error_list) == 4
        assert error_check('hook_error', error_list)
        assert error_check('mseq_error', error_list)
        assert error_check('reso_error', error_list)
        assert error_check('generation_error', error_list)
        # Let us move the pt2 back into the correct position
        get(pt2.pk).move(get(pinch2.pk), 'right')
        # The tree currently looks like this:
        #             Root
        # PT1 Reso Pinch1 Midp Pinch2 pt2 Hook
        # This violates milestone sequence, hook placement, and resolution placement.
        error_list = arc_sample.fetch_arc_errors()
        assert len(error_list) == 3
        assert error_check('hook_error', error_list)
        assert error_check('mseq_error', error_list)
        assert error_check('reso_error', error_list)
        beat = get(pt1.pk).add_sibling('right', arc_element_type='beat', description='I am a beat')
        # The tree currently looks like this:
        #             Root
        # PT1 beat Reso Pinch1 Midp Pinch2 pt2 hook
        # This violates milestone sequence, hook placement, and resolution placement.
        # Adding a beat should be fine.
        error_list = arc_sample.fetch_arc_errors()
        assert len(error_list) == 3
        assert error_check('hook_error', error_list)
        assert error_check('mseq_error', error_list)
        assert error_check('reso_error', error_list)
        tf = get(beat.pk).add_sibling('right', arc_element_type='tf', description='I am a try/fail cycle')
        # The tree currently looks like this:
        #             Root
        # PT1 beat tf reso Pinch1 Midp Pinch2 pt2 hook
        # This violates milestone sequence, hook placement, and resolution placement.
        error_list = arc_sample.fetch_arc_errors()
        assert len(error_list) == 3
        assert error_check('hook_error', error_list)
        assert error_check('mseq_error', error_list)
        assert error_check('reso_error', error_list)
        # Now we try to put the try/fail under a beat, which is not an allowed parent.
        get(tf.pk).move(get(beat.pk), 'first-child')
        # The tree currently looks like this.
        #             Root
        # PT1 beat reso Pinch1 Midp Pinch2 pt2 hook
        #     tf
        # This violates milestone sequence, hook placement, resolution placement,
        # and generation as Try/Fail cannot have a beat as a parent.
        error_list = arc_sample.fetch_arc_errors()
        assert len(error_list) == 4
        assert error_check('hook_error', error_list)
        assert error_check('mseq_error', error_list)
        assert error_check('reso_error', error_list)
        assert error_check('generation_error', error_list)
        # Try/Fails can't be inside a beat, only the other way around.
        get(tf.pk).move(get(beat.pk), 'right')  # Goes to the right of the beat.
        # Now put the beat underneath the try/fail.
        get(beat.pk).move(get(tf.pk), 'first-child')
        # The tree currently looks like this.
        #             Root
        # PT1 tf   reso pinch1 Midp pinch2 pt2 hook
        #     beat
        # This violates milestone sequence, hook placement, and resolution placement.
        error_list = arc_sample.fetch_arc_errors()
        assert len(error_list) == 3
        assert error_check('hook_error', error_list)
        assert error_check('mseq_error', error_list)
        assert error_check('reso_error', error_list)
        # Now add a nested TF under the existing TF. This should be allowed.
        tf2 = get(tf.pk).add_child(arc_element_type='tf', description='I am a nested try/fail cycle.')
        assert tf2
        # Now the tree looks like this.
        #             Root
        # PT1      tf        reso pinch1 midp pinch2 pt2 hook
        #       beat tf2
        # This violates milestone sequence, hook placement, and resolution placement.
        error_list = arc_sample.fetch_arc_errors()
        assert len(error_list) == 3  # Nesting try/fail is allowed.
        assert error_check('hook_error', error_list)
        assert error_check('mseq_error', error_list)
        assert error_check('reso_error', error_list)
        # Now put the original tf under a milestone
        get(tf.pk).move(get(pt1.pk), 'first-child')
        # Now the tree looks like this.
        #               Root
        #      PT1          Reso Pinch1 Midp Pinch2 pt2 hook
        #      tf
        #   beat tf2
        # This violates milestone sequence, hook placement, and resolution placement,
        # but is otherwise valid.
        assert get(pt1.pk).get_descendants().count() == 3
        # All of the tf's children should have moved under this.

        def test_character_location_origin(self):
            '''
            Ensures that the validation for keeping like outline
            objects together is enforced.
            '''
            arc = self.ms1.create_arc(mace_type='event', name='BOOM')
            arc_nodes = arc.arc_root_node.get_children()
            test_node = arc_nodes[0]
            with pytest.raises(IntegrityError):
                test_node.assoc_characters.add(self.char2_int)
            with pytest.raises(IntegrityError):
                self.char2_int.arcelementnode_set.add(test_node)
            with pytest.raises(IntegrityError):
                test_node.assoc_locations.add(self.loc3_int)
            with pytest.raises(IntegrityError):
                self.loc3_int.arcelementnode_set.add(test_node)

        def test_arc_and_story_node_same_outline(self):
            '''
            Ensures that an arc element node can't be linked
            to story node from different outline.
            '''
            story_node_count = StoryElementNode.objects.filter(outline=self.ms2)
            assert story_node_count == 1
            story_root_node = StoryElementNode.objects.get(outline=self.ms2)
            story_node = story_root_node.add_child(story_element_type='chapter')
            arc = self.ms1.create_arc(mace_type='event', name='KABLAMO')
            arc_nodes = arc.arc_root_node.get_children()
            test_node = arc_nodes[0]
            with pytest.raises(IntegrityError):
                test_node.story_element_node = story_node
                test_node.save()
            with pytest.raises(IntegrityError):
                story_node.arcelementnode_set.add(test_node)


class StoryTreeModelTest(TestCase):
    '''
    Tests for the story tree model.
    '''
    def setUp(self):
        '''
        Create users and base outlines for tests
        '''
        self.user1 = self.make_user('u1')
        self.user2 = self.make_user('u2')
        self.ms1 = Outline(
            title="Monkeys are here",
            description="A sample outline",
            user=self.user1
        )
        self.ms2 = Outline(title="A wild rabbit", description="Let's make stew", user=self.user2)
        self.ms1.save()
        self.ms2.save()
        self.arc = self.ms1.create_arc(mace_type='event', name='An example arc')
        self.char1 = Character(name="John Doe", user=self.user1)
        self.char1.save()
        self.char2 = Character(name='Jane Smith', user=self.user2)
        self.char2.save()
        self.loc1 = Location(name='Work', user=self.user1)
        self.loc1.save()
        self.loc2 = Location(name='Home', user=self.user1)
        self.loc2.save()
        self.char1_int = CharacterInstance(character=self.char1, outline=self.ms1)
        self.char1_int.save()
        self.char2_int = CharacterInstance(character=self.char2, outline=self.ms1)
        self.char2_int.save()
        self.char3 = Character(name="The shadow", user=self.user1)
        self.char3.save()
        self.char3_int = CharacterInstance(character=self.char3, outline=self.ms1)
        self.char3_int.save()
        self.loc1_int = LocationInstance(location=self.loc1, outline=self.ms1)
        self.loc1_int.save()
        self.loc2_int = LocationInstance(location=self.loc2, outline=self.ms1)
        self.loc2_int.save()
        self.loc3 = Location(name='Haunted Grocery', user=self.user1)
        self.loc3.save()
        self.loc3_int = LocationInstance(location=self.loc3, outline=self.ms1)
        self.loc3_int.save()
        self.loc4 = Location(name='The damn bar', user=self.user2)
        self.loc4.save()
        self.loc4_int = LocationInstance(location=self.loc4, outline=self.ms2)
        self.loc4_int.save()
        self.char4 = Character(name='Sneaky Pete', user=self.user2)
        self.char4.save()
        self.char4_int = CharacterInstance(character=self.char4, outline=self.ms2)
        self.char4_int.save()
        self.arc_nodes = self.arc.arc_root_node.get_children()
        self.arc_nodes[0].assoc_characters.add(self.char1_int)
        self.arc_nodes[1].assoc_characters.add(self.char2_int)
        self.arc_nodes[2].assoc_characters.add(self.char2_int)
        self.arc_nodes[0].assoc_locations.add(self.loc1_int)
        self.arc_nodes[1].assoc_locations.add(self.loc2_int)
        self.arc_nodes[2].assoc_locations.add(self.loc2_int)

    def test_inital_tree_created(self):
        '''
        Verifies that creating a outline has also created
        the root story node (which the user never sees), and
        only that root node should exist.
        '''
        assert self.ms1.story_tree_root
        assert StoryElementNode.objects.filter(outline=self.ms1).count() == 1
        assert StoryElementNode.objects.get(outline=self.ms1).is_root()
        assert StoryElementNode.objects.filter(outline=self.ms2).count() == 1
        assert StoryElementNode.objects.get(outline=self.ms2).is_root()

    def test_story_node_add_arc_element(self):
        '''
        Tests that character and location list is updated as additional arc_element_nodes are updated.
        '''
        story_root = StoryElementNode.objects.get(outline=self.ms1)
        chap1 = story_root.add_child(story_element_type='chapter', outline=self.ms1)
        chap2 = story_root.add_child(story_element_type='chapter', outline=self.ms1)

        def get(node_id): return StoryElementNode.objects.get(node_id)
        arc_node_test = self.arc_nodes[0]
        assert chap1.assoc_characters.count() == 0
        assert chap1.assoc_locations.count() == 0
        assert chap2.assoc_characters.count() == 0
        assert chap2.assoc_locations.count() == 0
        arc_node_test.story_element_node = chap1
        arc_node_test.save()
        assert arc_node_test.assoc_characters.count() == 1
        chap1.refresh_from_db()
        assert chap1.assoc_characters.count() == 1
        assert chap1.assoc_locations.count() == 1
        arc_node_test2 = self.arc_nodes[1]
        arc_node_test2.story_element_node = chap2
        arc_node_test2.save()
        chap2.refresh_from_db()
        assert chap2.assoc_characters.count() == 1
        assert chap2.assoc_locations.count() == 1
        arc2 = self.ms1.create_arc(mace_type='character', name='A mysterious love interest')
        arc2_nodes = arc2.arc_root_node.get_children()
        arc2_node1 = arc2_nodes[0]
        arc2_node2 = arc2_nodes[1]
        arc2_node1.assoc_characters.add(self.char2_int)
        arc2_node1.assoc_locations.add(self.loc2_int)
        arc2_node2.assoc_characters.add(self.char1_int)
        arc2_node2.assoc_locations.add(self.loc1_int)
        arc2_node1.story_element_node = chap1
        arc2_node1.save()
        chap1.refresh_from_db()
        assert chap1.assoc_characters.count() == 2
        assert chap1.assoc_locations.count() == 2
        arc2_node2.story_element_node = chap1
        arc2_node2.save()
        chap1.refresh_from_db()
        assert chap1.assoc_characters.count() == 2
        assert chap1.assoc_locations.count() == 2
        arc2_node2.story_element_node = None
        arc2_node2.save()
        chap1.refresh_from_db()
        assert chap1.assoc_characters.count() == 2
        assert chap1.assoc_locations.count() == 2

    def test_story_node_on_arc_element_change(self):
        '''
        Tests that story node updates when the characters and locations of
        a linked arc element are updated.
        '''
        def get(node_id): return StoryElementNode.objects.get(pk=node_id)
        story_root = StoryElementNode.objects.get(outline=self.ms1)
        print(story_root)
        chap1 = get(story_root.pk).add_child(story_element_type='chapter', outline=self.ms1)
        chap2 = get(story_root.pk).add_child(story_element_type='chapter', outline=self.ms1)
        assert get(chap1.pk).assoc_characters.count() == 0
        assert get(chap1.pk).assoc_locations.count() == 0
        assert get(chap2.pk).assoc_characters.count() == 0
        assert get(chap2.pk).assoc_locations.count() == 0
        assert self.arc_nodes[0].assoc_characters.count() == 1
        print('chap1 pk %s' % chap1.pk)
        arc_node_test = self.arc_nodes[0]
        arc_node_test.story_element_node = get(chap1.pk)
        arc_node_test.save()
        print(model_to_dict(arc_node_test, fields=[field.name for field in arc_node_test._meta.fields]))
        chap1.refresh_from_db()
        print('Chap1: %s' % model_to_dict(chap1, fields=[field.name for field in chap1._meta.fields]))
        assert get(chap1.pk).assoc_characters.count() == 1
        assert get(chap1.pk).assoc_locations.count() == 1
        arc_node_test.assoc_characters.add(self.char2_int)
        chap1.refresh_from_db()
        assert get(chap1.pk).assoc_characters.count() == 2
        arc_node_test.assoc_locations.add(self.loc2_int)
        chap1.refresh_from_db()
        assert get(chap1.pk).assoc_locations.count() == 2
        arc_node_test.assoc_locations.remove(self.loc2_int)
        chap1.refresh_from_db()
        assert get(chap1.pk).assoc_locations.count() == 2
        arc_node_test.assoc_characters.remove(self.char2_int)
        chap1.refresh_from_db()
        assert get(chap1.pk).assoc_characters.count() == 2
        self.char3_int.arcelementnode_set.add(arc_node_test)
        chap1.refresh_from_db()
        assert chap1.assoc_characters.count() == 3
        self.loc3_int.arcelementnode_set.add(arc_node_test)
        chap1.refresh_from_db()
        assert chap1.assoc_locations.count() == 3

    def test_require_char_loc_same_outline(self):
        '''
        Test that the story element node does not permit a
        character or location instance from a different outline.
        '''

        def get(node_id): return StoryElementNode.objects.get(pk=node_id)
        story_root = StoryElementNode.objects.get(outline=self.ms1)
        story_node = story_root.add_child(story_element_type='chapter', outline=self.ms1)
        # Wrapping in try statements per this:
        # https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom
        try:
            with transaction.atomic():
                with pytest.raises(IntegrityError):
                    get(story_node.pk).assoc_characters.add(self.char4_int)
        except(IntegrityError):
            pass
        try:
            with transaction.atomic():
                with pytest.raises(IntegrityError):
                    self.char4_int.storyelementnode_set.add(story_node)
        except(IntegrityError):
            pass
        try:
            with transaction.atomic():
                with pytest.raises(IntegrityError):
                    get(story_node.pk).assoc_locations.add(self.loc4_int)
        except(IntegrityError):
            pass
        try:
            with transaction.atomic():
                with pytest.raises(IntegrityError):
                    self.loc4_int.storyelementnode_set.add(story_node)
        except(IntegrityError):
            pass

    def test_story_node_on_descendant_updated(self):
        '''
        Test that a parent story node returns the values for characters, locations,
        arc elements, etc from all of it's descendant nodes.
        '''
        def get(node_id): return StoryElementNode.objects.get(pk=node_id)
        story_root = StoryElementNode.objects.get(outline=self.ms1)
        book1 = story_root.add_child(story_element_type='book', name='book1')
        act1 = get(book1.pk).add_child(story_element_type='act', name='act1')
        part1 = get(act1.pk).add_child(story_element_type='part', name='Part 1')
        chap1 = get(part1.pk).add_child(story_element_type='chapter', name='chapter 1')
        chap2 = get(part1.pk).add_child(story_element_type='chapter', name='chapter 2')
        scene1 = get(chap1.pk).add_child(story_element_type='ss')
        for node in get(story_root.pk).get_descendants():
            assert node.assoc_characters.count() == 0
            assert node.assoc_locations.count() == 0
        for node in get(story_root.pk).get_descendants():
            assert node.all_characters.count() == 0
            assert node.all_locations.count() == 0
        get(chap1.pk).assoc_characters.add(self.char1_int)
        assert get(chap1.pk).all_characters.count() == get(chap1.pk).assoc_characters.count()
        assert get(part1.pk).all_characters.count() == get(chap1.pk).all_characters.count()
        scene1.assoc_characters.add(self.char2_int)
        assert get(scene1.pk).assoc_characters.count() == get(scene1.pk).all_characters.count()
        assert get(scene1.pk).assoc_characters.count() == 1
        assert get(chap1.pk).assoc_characters.count() == 1
        assert get(chap1.pk).all_characters.count() == 2
        assert get(chap1.pk).all_characters.count() == get(part1.pk).all_characters.count()
        chap2.assoc_characters.add(self.char3_int)
        assert (get(chap2.pk).all_characters.count() == get(chap2.pk).assoc_characters.count() and
                get(chap2.pk).all_characters.count() == 1)
        assert get(chap1.pk).all_characters.count() == 2
        assert get(part1.pk).all_characters.count() == 3
        assert get(part1.pk).assoc_characters.count() == 0
        assert get(act1.pk).assoc_characters.count() == 0 and get(act1.pk).all_characters.count() == 3
        assert get(book1.pk).assoc_characters.count() == 0 and get(book1.pk).all_characters.count() == 3
        get(chap2.pk).assoc_characters.remove(self.char3_int)
        assert get(book1.pk).all_characters.count() == 2
        assert get(part1.pk).all_characters.count() == 2
        assert get(act1.pk).all_characters.count() == 2
        assert get(chap2.pk).all_characters.count() == 0
        # A duplicate should not get counted
        get(chap2.pk).assoc_characters.add(self.char1_int)
        assert get(part1.pk).all_characters.count() == 2
        assert get(act1.pk).all_characters.count() == 2
        assert get(book1.pk).all_characters.count() == 2
        # Now do the same checks for locations
        get(chap1.pk).assoc_locations.add(self.loc1_int)
        get(scene1.pk).assoc_locations.add(self.loc2_int)
        assert get(scene1.pk).all_locations.count() == get(scene1.pk).assoc_locations.count()
        assert get(chap1.pk).all_locations.count() == 2
        assert get(chap1.pk).assoc_locations.count() == 1
        get(chap2.pk).assoc_locations.add(self.loc3_int)
        assert get(chap2.pk).assoc_locations.count() == get(chap2.pk).all_locations.count()
        assert get(chap2.pk).all_locations.count() == 1
        assert get(part1.pk).all_locations.count() == 3
        assert get(act1.pk).all_locations.count() == 3
        assert get(book1.pk).all_locations.count() == 3
        get(chap2.pk).assoc_locations.remove(self.loc3_int)
        assert get(book1.pk).all_locations.count() == 2
        assert get(act1.pk).all_locations.count() == 2
        assert get(part1.pk).all_locations.count() == 2
        get(chap2.pk).assoc_locations.add(self.loc1_int)
        # A duplicate should not get counted twice.
        assert get(part1.pk).all_locations.count() == 2
        assert get(act1.pk).all_locations.count() == 2
        assert get(book1.pk).all_locations.count() == 2

    def test_story_element_generation_rules_for_move(self):
        '''
        Verify that allowed_parents rules are enforced for story element nodes.
        '''
        def get(node_id): return StoryElementNode.objects.get(pk=node_id)
        story_root = StoryElementNode.objects.get(outline=self.ms1)
        with pytest.raises(IntegrityError):
            story_root.add_child(story_element_type='book', outline=self.ms2)
        book1 = story_root.add_child(story_element_type='book', outline=self.ms1)
        part1 = book1.add_child(story_element_type='part')
        scene1 = get(book1.pk).add_child(story_element_type='ss')
        chap1 = get(book1.pk).add_child(story_element_type='chapter')
        act1 = get(book1.pk).add_child(story_element_type='act')
        with pytest.raises(IntegrityError):
            get(act1.pk).move(target=scene1, pos='first-child')
        with pytest.raises(IntegrityError):
            get(act1.pk).move(target=part1, pos='first-child')
        with pytest.raises(IntegrityError):
            get(act1.pk).move(target=chap1, pos='first-child')
        get(scene1.pk).move(target=chap1, pos='first-child')
        with pytest.raises(IntegrityError):
            get(act1.pk).move(target=get(scene1.pk), pos='right')
        with pytest.raises(IntegrityError):
            get(act1.pk).move(target=get(scene1.pk), pos='left')
        with pytest.raises(IntegrityError):
            get(act1.pk).move(target=get(scene1.pk), pos='first-sibling')
        with pytest.raises(IntegrityError):
            get(act1.pk).move(target=get(scene1.pk), pos='last-sibling')

    def test_story_element_generation_rules_for_creation(self):
        '''
        Tests that allowed parents rules are enforced when creating nodes.
        '''
        def get(node_id): return StoryElementNode.objects.get(pk=node_id)
        story_root = StoryElementNode.objects.get(outline=self.ms1)
        with pytest.raises(IntegrityError):
            story_root.add_child(story_element_type='book', outline=self.ms2)
        book1 = story_root.add_child(story_element_type='book')
        chap1 = get(story_root.pk).add_child(story_element_type='chapter')
        scene1 = get(book1.pk).add_child(story_element_type='ss')
        scene2 = get(chap1.pk).add_child(story_element_type='ss')
        with pytest.raises(IntegrityError):
            get(scene1.pk).add_child(story_element_type='chapter')
        with pytest.raises(IntegrityError):
            get(scene2.pk).add_sibling(story_element_type='act', pos='right')
        with pytest.raises(IntegrityError):
            get(scene2.pk).add_sibling(story_element_type='act', pos='left')
        with pytest.raises(IntegrityError):
            get(scene2.pk).add_sibling(story_element_type='act', pos='first_sibling')
        with pytest.raises(IntegrityError):
            get(scene2.pk).add_sibling(story_element_type='act', pos='last_sibling')


class MaceOutlineNestingTestCase(TestCase):
    '''
    A test case for verfifying that the MACE nesting principles, and story structure rules are
    checked.
    '''
    pass


class OutlineEstimateTestCase(TestCase):
    '''
    A test case for verifying that the Outline length estimator is working correctly.
    '''
    def setUp(self):
        '''
        Create users and base outlines for tests
        '''
        self.user1 = self.make_user('u1')
        self.user2 = self.make_user('u2')
        self.ms1 = Outline(
            title="Monkeys are here",
            description="A sample outline",
            user=self.user1
        )
        self.ms2 = Outline(title="A wild rabbit", description="Let's make stew", user=self.user1)
        self.ms1.save()
        self.ms2.save()
        self.ms1.create_arc(mace_type='event', name='Zombies!')
        self.ms2.create_arc(mace_type='event', name='Like sharknado, but with sturgeon')
        self.char1 = Character(name="John Doe", user=self.user1)
        self.char1.save()
        self.char2 = Character(name='Jane Smith', user=self.user1)
        self.char2.save()
        self.loc1 = Location(name='Work', user=self.user1)
        self.loc1.save()
        self.loc2 = Location(name='Home', user=self.user1)
        self.loc2.save()
        self.char1_int = CharacterInstance(character=self.char1, outline=self.ms1)
        self.char1_int.save()
        self.char2_int = CharacterInstance(character=self.char2, outline=self.ms2)
        self.char2_int.save()
        self.char3 = Character(name="The shadow", user=self.user1)
        self.char3.save()
        self.char3_int = CharacterInstance(character=self.char3, outline=self.ms2)
        self.char3_int.save()
        self.loc1_int = LocationInstance(location=self.loc1, outline=self.ms1)
        self.loc1_int.save()
        self.loc2_int = LocationInstance(location=self.loc2, outline=self.ms2)
        self.loc2_int.save()
        self.loc3 = Location(name='Haunted Grocery', user=self.user1)
        self.loc3.save()
        self.loc3_int = LocationInstance(location=self.loc3, outline=self.ms2)
        self.loc3_int.save()

    def test_initial_estimates(self):
        '''
        Tests that we initiate from setup with the correct length estimate.
        '''
        verified_length_ms1 = ((1 + 1) * 750) * (1.5 * 1)  # The correct length for ms1
        verified_length_ms2 = ((2 + 2) * 750) * (1.5 * 1)  # The correct length for ms2
        assert self.ms1.length_estimate == verified_length_ms1
        assert self.ms2.length_estimate == verified_length_ms2

    def test_add_arc(self):
        '''
        Verify that incrementing the number of arcs correctly increases estimate.
        '''
        verified_length_ms1 = ((1 + 1) * 750) * (1.5 * 2)
        verified_length_ms2 = ((2 + 2) * 750) * (1.5 * 2)
        self.ms1.create_arc(mace_type='character', name='mental illness')
        self.ms2.create_arc(mace_type='milieu', name='Boarding school')
        self.ms1.refresh_from_db()
        self.ms2.refresh_from_db()
        assert self.ms1.length_estimate == verified_length_ms1
        assert self.ms2.length_estimate == verified_length_ms2

    def test_remove_arc(self):
        '''
        Verify that removing an arc increases the count accordingly.
        '''
        arc2 = self.ms2.create_arc(mace_type='event', name='poodles!')
        assert arc2
        arc3 = self.ms2.create_arc(mace_type='answer', name='who let out the poodles?')
        self.ms2.refresh_from_db()
        assert self.ms2.length_estimate == ((2 + 2) * 750) * (1.5 * 3)
        arc1 = Arc.objects.get(outline=self.ms1)
        arc1.delete()
        self.ms1.refresh_from_db()
        assert self.ms1.length_estimate == 0
        arc3.delete()
        self.ms2.refresh_from_db()
        assert self.ms2.length_estimate == ((2 + 2) * 750) * (1.5 * 2)

    def test_add_character_instance(self):
        '''
        Verify that adding a character instance increases estimate correctly.
        '''
        verified_length_ms1 = ((2 + 1) * 750) * (1.5 * 1)
        verified_length_ms2 = ((3 + 2) * 750) * (1.5 * 1)
        char4 = Character(name='Nerdy best friend', user=self.user1)
        char4.save()
        char4_int = CharacterInstance(character=char4, outline=self.ms1)
        char4_int.save()
        char4_int2 = CharacterInstance(character=char4, outline=self.ms2)
        char4_int2.save()
        self.ms1.refresh_from_db()
        self.ms2.refresh_from_db()
        assert self.ms1.length_estimate == verified_length_ms1
        assert self.ms2.length_estimate == verified_length_ms2

    def test_remove_character_instance(self):
        '''
        Verify that removing a character updates the length estimate correctly.
        '''
        verified_length_ms1 = ((0 + 1) * 750) * (1.5 * 1)
        verified_length_ms2 = ((1 + 2) * 750) * (1.5 * 1)
        self.char1_int.delete()
        self.char2_int.delete()
        self.ms1.refresh_from_db()
        self.ms2.refresh_from_db()
        assert self.ms1.length_estimate == verified_length_ms1
        assert self.ms2.length_estimate == verified_length_ms2

    def test_add_location_instance(self):
        '''
        Verify that adding a location instance increased the estimate.
        '''
        verified_length_ms1 = ((1 + 2) * 750) * (1.5 * 1)
        verified_length_ms2 = ((2 + 3) * 750) * (1.5 * 1)
        loc4 = Location(name='the basket', user=self.user1)
        loc4.save()
        loc4_int = LocationInstance(location=loc4, outline=self.ms1)
        loc4_int.save()
        loc4_int2 = LocationInstance(location=loc4, outline=self.ms2)
        loc4_int2.save()
        self.ms1.refresh_from_db()
        self.ms2.refresh_from_db()
        assert self.ms1.length_estimate == verified_length_ms1
        assert self.ms2.length_estimate == verified_length_ms2

    def test_remove_location_instance(self):
        '''
        Verify that removing a location instance updates estimate correctly.
        '''
        verified_length_ms1 = ((1 + 0) * 750) * (1.5 * 1)
        verified_length_ms2 = ((2 + 1) * 750) * (1.5 * 1)
        self.loc3_int.delete()
        self.loc1_int.delete()
        self.ms1.refresh_from_db()
        self.ms2.refresh_from_db()
        assert self.ms1.length_estimate == verified_length_ms1
        assert self.ms2.length_estimate == verified_length_ms2


class MACENestTest(TestCase):
    '''
    Test validation for MACE nesting within the story tree.
    '''

    def setUp(self):
        '''
        Create users and base outlines for tests
        '''
        self.user1 = self.make_user('u1')
        self.user2 = self.make_user('u2')
        self.ms1 = Outline(
            title="Monkeys are here",
            description="A sample outline",
            user=self.user1
        )
        self.ms2 = Outline(title="A wild rabbit", description="Let's make stew", user=self.user1)
        self.ms1.save()
        self.ms2.save()
        self.ms1.create_arc(mace_type='event', name='Zombies!')
        self.ms2.create_arc(mace_type='event', name='Like sharknado, but with sturgeon')
        self.char1 = Character(name="John Doe", user=self.user1)
        self.char1.save()
        self.char2 = Character(name='Jane Smith', user=self.user1)
        self.char2.save()
        self.loc1 = Location(name='Work', user=self.user1)
        self.loc1.save()
        self.loc2 = Location(name='Home', user=self.user1)
        self.loc2.save()
        self.char1_int = CharacterInstance(character=self.char1, outline=self.ms1)
        self.char1_int.save()
        self.char2_int = CharacterInstance(character=self.char2, outline=self.ms2)
        self.char2_int.save()
        self.char3 = Character(name="The shadow", user=self.user1)
        self.char3.save()
        self.char3_int = CharacterInstance(character=self.char3, outline=self.ms2)
        self.char3_int.save()
        self.loc1_int = LocationInstance(location=self.loc1, outline=self.ms1)
        self.loc1_int.save()
        self.loc2_int = LocationInstance(location=self.loc2, outline=self.ms2)
        self.loc2_int.save()
        self.loc3 = Location(name='Haunted Grocery', user=self.user1)
        self.loc3.save()
        self.loc3_int = LocationInstance(location=self.loc3, outline=self.ms2)
        self.loc3_int.save()

    def testArcNestValidation(self):
        '''
        Examines all the arcs in a story tree and warns if the order of resolution is
        anything other than the exact opposite order of the introduction of the hooks.
        '''
        story_root = self.ms1.story_tree_root

        def get_st(node_id): return StoryElementNode.objects.get(pk=node_id)

        def get_ae(node_id): return ArcElementNode.objects.get(pk=node_id)
        part1 = story_root.add_child(story_element_type='part')
        part2 = get_st(story_root.pk).add_child(story_element_type='part')
        chap1 = get_st(part1.pk).add_child(story_element_type='chapter')
        chap2 = get_st(part1.pk).add_child(story_element_type='chapter')
        chap3 = get_st(part2.pk).add_child(story_element_type='chapter')
        chap4 = get_st(part2.pk).add_child(story_element_type='chapter')
        scenes = {}
        x = 1
        for chap in [chap1, chap2, chap3, chap4]:
            for y in range(4):
                scenes['scene %d' % x] = get_st(chap.pk).add_child(story_element_type='ss')
                x += 1
        # Now create three arcs
        arc1 = self.ms1.create_arc(mace_type='character', name='coming of age')
        arc2 = self.ms1.create_arc(mace_type='event', name='A QUEST!!!')
        arc3 = self.ms1.create_arc(mace_type='event', name='invading dragons')
        # ok, so we have our arcs. let's add a hook.
        arc1hook = ArcElementNode.objects.get(arc=arc1, arc_element_type='mile_hook')
        arc1hook.story_element_node = scenes['scene 1']
        arc1hook.save()
        assert self.ms1.validate_nesting() == {}  # Empty error list.
        arc1reso = ArcElementNode.objects.get(arc=arc1, arc_element_type='mile_reso')
        arc1reso.story_element_node = scenes['scene 14']
        arc1reso.save()
        assert self.ms1.validate_nesting() == {}  # Empty error list
        arc2reso = ArcElementNode.objects.get(arc=arc2, arc_element_type='mile_reso')
        arc2reso.story_element_node = scenes['scene 15']
        arc2reso.save()
        assert arc2reso.is_milestone
        assert self.ms1.validate_nesting() == {}  # Empty error list
        arc2hook = ArcElementNode.objects.get(arc=arc2, arc_element_type='mile_hook')
        arc2hook.story_element_node = scenes['scene 2']
        arc2hook.save()
        error_dict = self.ms1.validate_nesting()
        assert len(error_dict.keys()) == 1  # Arcs resolve in the wrong order.
        assert (error_dict['nest_reso_error']['error_message'] ==
                "Arcs should resolve in the opposite order that they were introduced")
        assert (list(error_dict['nest_reso_error']['offending_nodes']) ==
                [get_st(scenes['scene 14'].pk), get_st(scenes['scene 15'].pk)])
        # Ok, let's fix the error and see if all is better.
        arc1reso.refresh_from_db()
        arc1reso.story_element_node = get_st(scenes['scene 15'].pk)
        arc1reso.save()
        assert self.ms1.validate_nesting() == {}  # Resolving at the same time is fine.
        # Now we'll put arc 2 a little earlier
        arc2reso.refresh_from_db()
        arc2reso.story_element_node = get_st(scenes['scene 14'].pk)
        arc2reso.save()
        assert self.ms1.validate_nesting() == {}
        # Now put in the resolution for arc3
        arc3reso = ArcElementNode.objects.get(arc=arc3, arc_element_type='mile_reso')
        arc3reso.story_element_node = get_st(scenes['scene 16'].pk)
        arc3reso.save()
        assert self.ms1.validate_nesting() == {}  # No hook, so not enough info to evaluate yet.
        arc3hook = ArcElementNode.objects.get(arc=arc3, arc_element_type='mile_hook')
        arc3hook.story_element_node = get_st(scenes['scene 3'].pk)
        arc3hook.save()
        error_dict = self.ms1.validate_nesting()
        assert (list(error_dict['nest_reso_error']['offending_nodes']) ==
                [get_st(scenes['scene 14'].pk), get_st(scenes['scene 15'].pk), get_st(scenes['scene 16'].pk)])
        arc3hook.refresh_from_db()
        # Starting at the same time as arc2 shoudl resolve the conflict between arc2 and arc3
        arc3hook.story_element_node = get_st(scenes['scene 2'].pk)
        arc3hook.save()
        error_dict = self.ms1.validate_nesting()
        assert (list(error_dict['nest_reso_error']['offending_nodes']) ==
                [get_st(scenes['scene 15'].pk), get_st(scenes['scene 16'].pk)])
        # Reset
        arc3reso.refresh_from_db()
        arc3reso.story_element_node = get_st(scenes['scene 12'].pk)
        arc3reso.save()
        assert self.ms1.validate_nesting() == {}
        # Now let's toss in some ordering within the same arc. All we care about is milestone sequence.
        arc1mid = ArcElementNode.objects.get(arc=arc1, arc_element_type='mile_mid')
        arc1mid.story_element_node = get_st(scenes['scene 8'].pk)
        arc1mid.save()
        assert self.ms1.validate_nesting() == {}
        arc1pt2 = ArcElementNode.objects.get(arc=arc1, arc_element_type='mile_pt2')
        arc1pt2.story_element_node = get_st(scenes['scene 5'].pk)
        arc1pt2.save()
        error_dict = self.ms1.validate_nesting()
        assert error_dict['nest_arc_seq']['error_message'] == "Arc element milestones are out of sequence"
        assert (list(error_dict['nest_arc_seq']['offending_arcs'][0]['offending_nodes']) ==
                [
                    get_st(scenes['scene 1'].pk),
                    get_st(scenes['scene 5'].pk),
                    get_st(scenes['scene 8'].pk),
                    get_st(scenes['scene 15'].pk)])

    def testStoryImpactCalculation(self):
        '''
        Evaluates that the impact calculator properly measures the intensity of the
        story when milestones from multiple arcs overlap close to each other.

        Impact is measured as such:
        base_impact = 0.5
        arc_beat = 0.5
        arc_beat_that_descends_from_milestone = 1
        arc_milestone = 2
        same_miletstone_from_another_arc = 2.5
        There is also generational bleed based on the direct generational lines (not siblings)
        '''
        story_root = self.ms1.story_tree_root
        # Now we will create two parts and four chapters. Two chapters per part.

        def get_st(node_id): return StoryElementNode.objects.get(pk=node_id)

        def get_ae(node_id): return ArcElementNode.objects.get(pk=node_id)
        part1 = story_root.add_child(story_element_type='part')
        part2 = get_st(story_root.pk).add_child(story_element_type='part')
        chap1 = get_st(part1.pk).add_child(story_element_type='chapter')
        chap2 = get_st(part1.pk).add_child(story_element_type='chapter')
        chap3 = get_st(part2.pk).add_child(story_element_type='chapter')
        chap4 = get_st(part2.pk).add_child(story_element_type='chapter')
        # Now we add two scenes per chapter.
        scenes = {}
        x = 1
        for chap in [chap1, chap2, chap3, chap4]:
            scenes['scene %d' % x] = get_st(chap.pk).add_child(story_element_type='ss')
            x += 1
            scenes['scene %d' % x] = get_st(chap.pk).add_child(story_element_type='ss')
            x += 1
        # Now we have eight scenes to work with. Let's make our arcs.
        arc1 = self.ms1.create_arc(mace_type='character', name='Coming of age')
        arc2 = self.ms1.create_arc(mace_type='event', name='Invasion of the uptight people')
        arc3 = self.ms1.create_arc(mace_type='event', name='Escape from town')
        # Each of these arcs have seven milestones. In arc 1, we're also going to add a beat
        # as a child of the midpoint.
        arc1mid = ArcElementNode.objects.get(arc=arc1, arc_element_type='mile_mid')
        beat1 = get_ae(arc1mid.pk).add_child(arc_element_type='beat', description='Making a plan')
        # Now we'll make a beat that's a sibling of the milestones, which doesn't inherit
        # any extra awesomeness.
        beat2 = get_ae(arc1mid.pk).add_sibling(pos='left', arc_element_type='beat', description='exposition')
        # Now, we check the impact for all the elements of the story tree.
        for node in get_st(story_root.pk).get_descendants():
            assert node.impact_rating == 0.5
        # Now, let's associate the weak beat from arc one with scene 4, which is chapter 2.
        beat2.story_element_node = get_st(scenes['scene 4'].pk)
        beat2.save()
        assert get_st(scenes['scene 4'].pk).get_ancestors().count() == 3
        assert get_st(scenes['scene 4'].pk).impact_rating == 1
        assert get_st(chap2.pk).impact_rating == 0.625
        # Now let's add beat1 to scene 5. Note, it inherits some marginal
        # additional impact from the parent milestone, but since it is only
        # a piece of the puzzle we halve the potential extra benefit.
        beat1.refresh_from_db()
        beat1.story_element_node = get_st(scenes['scene 5'].pk)
        beat1.save()
        assert get_st(scenes['scene 5'].pk).impact_rating == 1.5
        # Let's look at the chapter impact.
        assert get_st(chap3.pk).impact_rating == 0.75
        # Now let's explicitly assign the midpoint to that chapter.
        arc1mid.refresh_from_db()
        arc1mid.story_element_node = get_st(chap3.pk)
        arc1mid.save()
        # Now let's check the intensity, both the immediate descendant, and the parent.
        assert get_st(chap3.pk).impact_rating == 2.75
        assert get_st(scenes['scene 5'].pk).impact_rating == 2.5
        # Now, let's add the plot turn 1 from arc 2 to scene 3
        arc2pt1 = ArcElementNode.objects.get(arc=arc2, arc_element_type='mile_pt1')
        arc2pt1.story_element_node = get_st(scenes['scene 3'].pk)
        arc2pt1.save()
        assert get_st(scenes['scene 3'].pk).impact_rating == 2.5
        assert get_st(chap2.pk).impact_rating == 1.625
        # Now let's apply the pinch1 from arc1 to that scene.
        arc1pinch1 = ArcElementNode.objects.get(arc=arc1, arc_element_type='mile_pnch1')
        arc1pinch1.story_element_node = get_st(scenes['scene 3'].pk)
        arc1pinch1.save()
        assert get_st(scenes['scene 3'].pk).impact_rating == 4.5
        assert get_st(chap2.pk).impact_rating == 2.625
        # Now add an arc milestone of the same type to scene 3
        arc3pinch1 = ArcElementNode.objects.get(arc=arc3, arc_element_type='mile_pnch1')
        arc3pinch1.story_element_node = get_st(scenes['scene 3'].pk)
        arc3pinch1.save()
        assert get_st(scenes['scene 3'].pk).impact_rating == 7  # Like milestones have greater intensity.
        assert get_st(chap2.pk).impact_rating == 3.75
        # Now we'll line up the arc 2 pinch 1 with beat 1, which will affect both the scene and the chapter
        arc2pinch1 = ArcElementNode.objects.get(arc=arc2, arc_element_type='mile_pnch1')
        arc2pinch1.story_element_node = get_st(scenes['scene 5'].pk)
        arc2pinch1.save()
        assert get_st(scenes['scene 5'].pk).impact_rating == 4.5
        assert get_st(chap3.pk).impact_rating == 3.75
        assert get_st(part2.pk).impact_rating == 2.0625
        assert get_st(part1.pk).impact_rating == 2.0625
