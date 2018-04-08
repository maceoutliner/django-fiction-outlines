# Generated by Django 2.0.4 on 2018-04-08 02:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import taggit.managers
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Arc',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('mace_type', models.CharField(choices=[('milieu', 'Milieu'), ('answer', 'Answers'), ('character', 'Character'), ('event', 'Event')], db_index=True, help_text='The MACE type of the Arc.', max_length=10)),
                ('name', models.CharField(db_index=True, help_text='Name of this Arc (makes it easier for you to keep track of it.)', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ArcElementNode',
            fields=[
                ('path', models.CharField(max_length=1024, unique=True)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('arc_element_type', models.CharField(choices=[('root', 'Arc Parent Node(user-hidden)'), ('mile_hook', 'Milestone: Hook'), ('mile_pt1', 'Milestone: Plot Turn 1'), ('mile_pnch1', 'Milestone: Pinch 1'), ('mile_mid', 'Milestone: Midpoint'), ('mile_pnch2', 'Milestone: Pinch 2'), ('mile_pt2', 'Milestone: Plot Turn 2'), ('mile_reso', 'Milestone: Resolution'), ('tf', 'Try/Fail'), ('beat', 'Beat')], db_index=True, help_text='What part of the arc does this represent?', max_length=15)),
                ('headline', models.CharField(blank=True, help_text='Autogenerated from description', max_length=255, null=True)),
                ('description', models.TextField(help_text='Describe what happens at this moment in the story...')),
                ('arc', models.ForeignKey(help_text='Parent arc.', on_delete=django.db.models.deletion.CASCADE, to='fiction_outlines.Arc')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Character',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, help_text='Name of the character.', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Notes about the character to help you remember.', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CharacterInstance',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('main_character', models.BooleanField(db_index=True, default=False, help_text='Is this character the main character for the outline?')),
                ('pov_character', models.BooleanField(db_index=True, default=False, help_text='Is this character a POV character?')),
                ('protagonist', models.BooleanField(db_index=True, default=False, help_text='Does this character serve as the protagonist for this outline?')),
                ('antagonist', models.BooleanField(db_index=True, default=False, help_text='Does this character serve as an antagonist for this outline?')),
                ('obstacle', models.BooleanField(db_index=True, default=False, help_text='Is this character an obstacle in the outline? (not antagonist)')),
                ('villain', models.BooleanField(db_index=True, default=False, help_text='Is the character a straight-out villain?')),
                ('character', models.ForeignKey(help_text='Reference to originating character object.', on_delete=django.db.models.deletion.CASCADE, to='fiction_outlines.Character')),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, help_text='Name of the location.', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Notes about the location to help you remember.', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LocationInstance',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('location', models.ForeignKey(help_text='Originating location object.', on_delete=django.db.models.deletion.CASCADE, to='fiction_outlines.Location')),
            ],
        ),
        migrations.CreateModel(
            name='Outline',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(db_index=True, help_text='Outline title. You can always change this later.', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Optionally, describe the story. Or use for notes.', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Series',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(db_index=True, help_text='Name of the series. You can always change this later.', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Jot down a description about your series.', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StoryElementNode',
            fields=[
                ('path', models.CharField(max_length=1024, unique=True)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, help_text='Optional name/title for this element of the story.', max_length=255, null=True)),
                ('description', models.TextField(blank=True, help_text='Optional description for this element of the story.', null=True)),
                ('story_element_type', models.CharField(choices=[('root', 'Root'), ('ss', 'Scene/Sequel'), ('chapter', 'Chapter'), ('part', 'Part'), ('act', 'Act'), ('book', 'Book')], db_index=True, default='ss', help_text='What part of the story does this represent? A scene? A chapter?', max_length=25)),
                ('assoc_characters', models.ManyToManyField(blank=True, help_text='Character instances associated with this node.', to='fiction_outlines.CharacterInstance', verbose_name='Associated Characters')),
                ('assoc_locations', models.ManyToManyField(blank=True, help_text='Location instances associated with this node.', to='fiction_outlines.LocationInstance', verbose_name='Associated Locations')),
                ('outline', models.ForeignKey(help_text='Parent outline.', on_delete=django.db.models.deletion.CASCADE, to='fiction_outlines.Outline')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UUIDCharacterTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.UUIDField(db_index=True, verbose_name='Object id')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fiction_outlines_uuidcharactertag_tagged_items', to='contenttypes.ContentType', verbose_name='Content type')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fiction_outlines_uuidcharactertag_items', to='taggit.Tag')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
        ),
        migrations.CreateModel(
            name='UUIDLocationTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.UUIDField(db_index=True, verbose_name='Object id')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fiction_outlines_uuidlocationtag_tagged_items', to='contenttypes.ContentType', verbose_name='Content type')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fiction_outlines_uuidlocationtag_items', to='taggit.Tag')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
        ),
        migrations.CreateModel(
            name='UUIDOutlineTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.UUIDField(db_index=True, verbose_name='Object id')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fiction_outlines_uuidoutlinetag_tagged_items', to='contenttypes.ContentType', verbose_name='Content type')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fiction_outlines_uuidoutlinetag_items', to='taggit.Tag')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
        ),
        migrations.AddField(
            model_name='series',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='Tags for the series.', through='fiction_outlines.UUIDOutlineTag', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='series',
            name='user',
            field=models.ForeignKey(help_text='The user that created this Series.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='outline',
            name='series',
            field=models.ForeignKey(blank=True, help_text='Belongs to series.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='fiction_outlines.Series'),
        ),
        migrations.AddField(
            model_name='outline',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='Tags for the outline.', through='fiction_outlines.UUIDOutlineTag', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='outline',
            name='user',
            field=models.ForeignKey(help_text='The user that created this outline.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='locationinstance',
            name='outline',
            field=models.ForeignKey(help_text='Outline this object is associated with.', on_delete=django.db.models.deletion.CASCADE, to='fiction_outlines.Outline'),
        ),
        migrations.AddField(
            model_name='location',
            name='series',
            field=models.ManyToManyField(blank=True, help_text='Series this location is associated with.', to='fiction_outlines.Series'),
        ),
        migrations.AddField(
            model_name='location',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='Tags for this location.', through='fiction_outlines.UUIDLocationTag', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='location',
            name='user',
            field=models.ForeignKey(help_text='The user that created this location.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='characterinstance',
            name='outline',
            field=models.ForeignKey(help_text='Outline this instance is associated with.', on_delete=django.db.models.deletion.CASCADE, to='fiction_outlines.Outline'),
        ),
        migrations.AddField(
            model_name='character',
            name='series',
            field=models.ManyToManyField(blank=True, help_text='If the character is part of a series, consider referencing it here.', to='fiction_outlines.Series'),
        ),
        migrations.AddField(
            model_name='character',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='Tags associated with this character. Yay, taxonomy!', through='fiction_outlines.UUIDCharacterTag', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='character',
            name='user',
            field=models.ForeignKey(help_text='The user that created this character.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='arcelementnode',
            name='assoc_characters',
            field=models.ManyToManyField(blank=True, help_text='M2M relation with character instances.', to='fiction_outlines.CharacterInstance', verbose_name='Associated Characters'),
        ),
        migrations.AddField(
            model_name='arcelementnode',
            name='assoc_locations',
            field=models.ManyToManyField(blank=True, help_text='M2M relation with location instances.', to='fiction_outlines.LocationInstance', verbose_name='Associated Locations'),
        ),
        migrations.AddField(
            model_name='arcelementnode',
            name='story_element_node',
            field=models.ForeignKey(blank=True, help_text='Which story node is this element associated with?', null=True, on_delete=django.db.models.deletion.SET_NULL, to='fiction_outlines.StoryElementNode'),
        ),
        migrations.AddField(
            model_name='arc',
            name='outline',
            field=models.ForeignKey(help_text='Arc belongs to this outline.', on_delete=django.db.models.deletion.CASCADE, to='fiction_outlines.Outline'),
        ),
        migrations.AlterUniqueTogether(
            name='locationinstance',
            unique_together={('location', 'outline')},
        ),
        migrations.AlterUniqueTogether(
            name='characterinstance',
            unique_together={('outline', 'character')},
        ),
    ]