'''
Views for fiction_outlines.
'''
import logging
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.db import IntegrityError, transaction
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic
from treebeard.exceptions import InvalidPosition, NodeAlreadySaved, PathOverflow, InvalidMoveToDescendant
from treebeard.forms import movenodeform_factory
from braces.views import SelectRelatedMixin, PrefetchRelatedMixin
from rules.contrib.views import PermissionRequiredMixin
from .models import Outline, Series, Character, CharacterInstance, Location, LocationInstance
from .models import Arc, ArcElementNode, StoryElementNode, ArcIntegrityError
from .signals import tree_manipulation
from . import forms

# Create your views here.

logger = logging.getLogger('fiction_outlines.view')
logger.setLevel(logging.DEBUG)


class SeriesListView(LoginRequiredMixin, generic.ListView):
    '''
    Generic view for viewing a list of series objects.
    '''
    model = Series
    template_name = "fiction_outlines/series_list.html"
    context_object_name = 'series_list'

    def get_queryset(self):
        return Series.objects.filter(user=self.request.user).prefetch_related(
            'character_set', 'location_set', 'outline_set')


class SeriesCreateView(LoginRequiredMixin, generic.CreateView):
    '''
    Generic view for creating series object.
    '''
    model = Series
    template_name = "fiction_outlines/series_create.html"
    fields = ['title', 'description', 'tags']
    success_url = None

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:series_detail', kwargs={'series': self.object.pk})

    def form_valid(self, form):
        '''
        Override to ensure we can add the user to the record.
        '''
        form.instance.user = self.request.user
        return super().form_valid(form)


class SeriesDetailView(LoginRequiredMixin, PermissionRequiredMixin, PrefetchRelatedMixin, generic.DetailView):
    '''
    Generic view to see series details.
    '''
    model = Series
    template_name = 'fiction_outlines/series_detail.html'
    prefetch_related = ['character_set', 'location_set', 'outline_set']
    permission_required = 'fiction_outlines.view_series'
    pk_url_kwarg = 'series'
    context_object_name = 'series'


class SeriesUpdateView(LoginRequiredMixin, PermissionRequiredMixin, PrefetchRelatedMixin, generic.edit.UpdateView):
    '''
    Generic view for updating a series object.
    '''
    model = Series
    template_name = 'fiction_outlines/series_update.html'
    permission_required = 'fiction_outlines.edit_series'
    fields = ['title', 'description', 'tags']
    prefetch_related = ['character_set', 'location_set', 'outline_set']
    success_url = None
    pk_url_kwarg = 'series'
    context_object_name = 'series'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:series_detail', kwargs={'series': self.object.id})


class SeriesDeleteView(LoginRequiredMixin, PermissionRequiredMixin, generic.edit.DeleteView):
    '''
    Generic view for deleting a series.
    '''
    model = Series
    permission_required = 'fiction_outlines.delete_series'
    template_name = 'fiction_outlines/series_delete.html'
    success_url = reverse_lazy('fiction_outlines:series_list')
    context_object_name = 'series'
    pk_url_kwarg = 'series'


class CharacterListView(LoginRequiredMixin, generic.ListView):
    '''
    Generic view for viewing character list.
    '''
    model = Character
    template_name = 'fiction_outlines/character_list.html'
    context_object_name = 'character_list'

    def get_queryset(self):
        return Character.objects.filter(user=self.request.user).prefetch_related(
            'characterinstance_set', 'characterinstance_set__outline', 'series')


class CharacterCreateView(LoginRequiredMixin, generic.CreateView):
    '''
    Generic view for creating a character.
    '''
    model = Character
    template_name = "fiction_outlines/character_create.html"
    form_class = forms.CharacterForm
    success_url = None

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:character_detail', kwargs={'character': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CharacterDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                          PrefetchRelatedMixin, generic.DetailView):
    '''
    Generic view for character details.
    '''
    model = Character
    template_name = 'fiction_outlines/character_detail.html'
    permission_required = 'fiction_outlines.view_character'
    prefetch_related = ['series', 'characterinstance_set', 'characterinstance_set__outline']
    pk_url_kwarg = 'character'
    context_object_name = 'character'


class CharacterUpdateView(LoginRequiredMixin, PermissionRequiredMixin, PrefetchRelatedMixin, generic.edit.UpdateView):
    '''
    Generic update view for character.
    '''
    model = Character
    template_name = 'fiction_outlines/character_update.html'
    permission_required = 'fiction_outlines.edit_character'
    form_class = forms.CharacterForm
    prefetch_related = ['series']
    success_url = None
    context_object_name = 'character'
    pk_url_kwarg = 'character'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:character_detail', kwargs={'character': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class CharacterDeleteView(LoginRequiredMixin, PermissionRequiredMixin, PrefetchRelatedMixin, generic.edit.DeleteView):
    '''
    Generic view for deleting a character.
    '''
    model = Character
    template_name = 'fiction_outlines/character_delete.html'
    permission_required = 'fiction_outlines.delete_character'
    success_url = reverse_lazy('fiction_outlines:character_list')
    prefetch_related = ['series', 'characterinstance_set']
    context_object_name = 'character'
    pk_url_kwarg = 'character'


class CharacterInstanceListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    '''
    Generic view for seeing a list of all character instances for a particular character.
    '''
    model = CharacterInstance
    permission_required = 'fiction_outlines.view_character'
    template_name = 'fiction_outlines/character_instance_list.html'
    context_object_name = 'character_instance_list'

    def dispatch(self, request, *args, **kwargs):
        self.character = get_object_or_404(Character, pk=kwargs['character'])
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.character

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['character'] = self.character
        return context

    def get_queryset(self):
        return CharacterInstance.objects.filter(character=self.character).select_related(
            'character', 'outline').prefetch_related('arcelementnode_set', 'storyelementnode_set')


class CharacterInstanceDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                                  SelectRelatedMixin, PrefetchRelatedMixin, generic.DetailView):
    '''
    Generic detail view for character instance.
    '''
    model = CharacterInstance
    permission_required = 'fiction_outlines.view_character'
    template_name = 'fiction_outlines/character_instance_detail.html'
    select_related = ['character', 'outline']
    prefetch_related = ['arcelementnode_set', 'storyelementnode_set']
    pk_url_kwarg = 'instance'
    context_object_name = 'character_instance'

    def dispatch(self, request, *args, **kwargs):
        self.character = get_object_or_404(Character, pk=kwargs['character'])
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.character


class CharacterInstanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    '''
    Generic create view for a character instance.
    '''
    model = CharacterInstance
    permission_required = None
    template_name = 'fiction_outlines/character_instance_create.html'
    form_class = forms.CharacterInstanceForm
    success_url = None
    outline = None

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:character_instance_detail', kwargs={'characterint': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['character'] = self.character
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.character = get_object_or_404(Character, pk=kwargs['character'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['character'] = self.character
        return context

    def has_permission(self):
        if self.outline:
            return (self.request.user.has_perm('fiction_outlines.edit_character', self.character) and
                    self.request.user.has_perm('fiction_outlines.edit_outline', self.outline))
        return self.request.user.has_perm('fiction_outlines.edit_character', self.character)

    def form_valid(self, form):
        self.outline = form.instance.outline
        form.instance.character = self.character
        if not self.has_permission():
            return HttpResponseForbidden()
        return super().form_valid(form)


class CharacterInstanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                                  SelectRelatedMixin, generic.edit.UpdateView):
    '''
    Generic view for updating a character instance.
    '''
    model = CharacterInstance
    permission_required = 'fiction_outlines.edit_character'
    template_name = 'fiction_outlines/character_instance_update.html'
    form_class = forms.CharacterInstanceForm
    select_related = ['character', 'outline']
    success_url = None
    pk_url_kwarg = 'instance'
    context_object_name = 'character_instance'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:character_instance_detail',
                            kwargs={'instance': self.object.pk, 'character': self.character})

    def dispatch(self, request, *args, **kwargs):
        self.character = get_object_or_404(Character, pk=kwargs['character'])
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.character

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['character'] = self.character
        return kwargs

    def form_valid(self, form):
        outline = form.instance.outline
        if not (self.request.user.has_perm('fiction_outlines.edit_character', self.character) and
                self.request.user.has_perm('fiction_outlines.edit_outline', outline)):
            return HttpResponseForbidden()
        return super().form_valid(form)


class CharacterInstanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin,
                                  SelectRelatedMixin, PrefetchRelatedMixin, generic.DeleteView):
    '''
    Generic view for deleting character instances.
    '''
    model = CharacterInstance
    template_name = 'fiction_outlines/character_instance_delete.html'
    permission_required = 'fiction_outlines.delete_character_instance'
    success_url = None
    select_related = ['character', 'outline']
    prefetch_related = ['arcelementnode_set', 'storyelementnode_set']
    context_object_name = 'character_instance'
    pk_url_kwarg = 'instance'

    def dispatch(self, request, *args, **kwargs):
        self.character = get_object_or_404(Character, pk=kwargs['character'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:character_detail', kwargs={'character': self.character.pk})


class LocationListView(LoginRequiredMixin, generic.ListView):
    '''
    Generic view for locations.
    '''
    model = Location
    template_name = 'fiction_outlines/location_list.html'
    context_object_name = "location_list"

    def get_queryset(self):
        return Location.objects.filter(user=self.request.user)


class LocationDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                         PrefetchRelatedMixin, generic.DetailView):
    '''
    Generic view for location details.
    '''
    model = Location
    template_name = 'fiction_outlines/location_detail.html'
    permission_required = 'fiction_outlines.view_location'
    prefetch_related = ['series', 'locationinstance_set', 'locationinstance_set__outline']
    pk_url_kwarg = 'location'
    context_object_name = 'location'


class LocationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.edit.UpdateView):
    '''
    Generic view for updating locations.
    '''
    model = Location
    permission_required = 'fiction_outlines.edit_location'
    template_name = 'fiction_outlines/location_update.html'
    form_class = forms.LocationForm
    success_url = None
    context_object_name = 'location'
    pk_url_kwarg = 'location'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:location_detail', kwargs={'location': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class LocationCreateView(LoginRequiredMixin, generic.CreateView):
    '''
    Generic view for creating locations
    '''
    model = Location
    template_name = 'fiction_outlines/location_create.html'
    form_class = forms.LocationForm
    success_url = None

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allowed_series'] = Series.objects.filter(user=self.request.user)
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class LocationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    '''
    Generic view for deleting locations.
    '''
    model = Location
    template_name = 'fiction_outlines/location_delete.html'
    permission_required = 'fiction_outlines.delete_location'
    success_url = None
    context_object_name = 'location'
    pk_url_kwarg = 'location'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:location_list')


class LocationInstanceListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    '''
    Generic view for looking at all location instances for a location.
    '''
    model = LocationInstance
    template_name = 'fiction_outlines/location_instance_list.html'
    permission_required = 'fiction_outlines.view_location'
    context_object_name = 'location_instance_list'

    def dispatch(self, request, *args, **kwargs):
        self.location = get_object_or_404(Location, pk=kwargs['location'])
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.location

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location'] = self.location
        return context

    def get_queryset(self):
        return LocationInstance.objects.filter(location=self.location).select_related(
            'location', 'outline').prefetch_related('arcelementnode_set', 'storyelementnode_set')


class LocationInstanceDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                                 SelectRelatedMixin, PrefetchRelatedMixin, generic.DetailView):
    '''
    Generic view for a location instance detail view.
    '''
    model = LocationInstance
    template_name = 'fiction_outlines/location_instance_detail.html'
    permission_required = 'fiction_outlines.view_location'
    select_related = ['location', 'outline']
    prefetch_related = ['arcelementnode_set', 'storyelementnode_set']
    pk_url_kwarg = 'instance'
    context_object_name = 'location_instance'

    def dispatch(self, request, *args, **kwargs):
        self.location = get_object_or_404(Location, pk=kwargs['location'])
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.location


class LocationInstanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    '''
    Generic view for creating a location instance on a outline.
    '''
    model = LocationInstance
    template_name = 'fiction_outlines/location_instance_create.html'
    permission_required = 'fiction_outlines.edit_location'
    success_url = None
    form_class = forms.LocationInstanceForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['location'] = self.location
        return kwargs

    def get_permission_object(self):
        return self.location

    def dispatch(self, request, *args, **kwargs):
        self.location = get_object_or_404(Location, pk=kwargs['location'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location'] = self.location
        return context

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:location_instance_detail',
                            kwargs={'location': self.location.pk, 'instance': self.object.pk})

    def form_valid(self, form):
        outline = form.instance.outline
        form.instance.location = self.location
        if not (self.request.user.has_perm('fiction_outlines.edit_location', self.location) and
                self.request.user.has_perm('fiction_outlines.edit_outline', outline)):
            return HttpResponseForbidden()
        return super().form_valid(form)


class LocationInstanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                                 SelectRelatedMixin, generic.edit.UpdateView):
    '''
    Generic view for updating a location instance. Not used since there are not details.
    But it's here if you want to subclass LocationInstance and customize it.
    '''
    model = LocationInstance
    # Blank template to override.
    template_name = 'fiction_outlines/location_instance_update.html'
    permission_required = 'fiction_outlines.edit_location_instance'
    success_url = None
    select_related = ['location', 'outline']
    form_class = forms.LocationInstanceForm
    context_object_name = 'location_instance'
    pk_url_kwarg = 'instance'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:location_instance_detail',
                            kwargs={'instance': self.object.pk, 'location': self.location.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['location'] = self.location
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.location = get_object_or_404(Location, pk=kwargs['location'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location'] = self.location
        return context

    def form_valid(self, form):
        outline = form.instance.outline
        if not (self.request.user.has_perm('fiction_outlines.edit_location', self.location) and
                self.request.user.has_perm('fiction_outlines.edit_outline', outline)):
            return HttpResponseForbidden()
        return super().form_valid(form)


class LocationInstanceDeleteView(LoginRequiredMixin, PermissionRequiredMixin,
                                 SelectRelatedMixin, PrefetchRelatedMixin, generic.DeleteView):
    '''
    Generic delete view for Location Instance.
    '''
    model = LocationInstance
    permission_required = 'fiction_outlines.delete_location_instance'
    template_name = 'fiction_outlines/location_instance_delete.html'
    success_url = None
    select_releated = ['location', 'outline']
    prefetch_related = ['arcelementnode_set', 'storyelementnode_set']
    context_object_name = 'location_instance'
    pk_url_kwarg = 'instance'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:location_details', kwargs={'location': self.location_id})

    def dispatch(self, request, *args, **kwargs):
        self.location = get_object_or_404(Location, pk=kwargs['location'])
        return super().dispatch(request, *args, **kwargs)


# TODO ArcElementNode, and StoryElementNode

class OutlineListView(LoginRequiredMixin, SelectRelatedMixin,
                      PrefetchRelatedMixin, generic.ListView):
    '''
    Generic view for Outline Outline list
    '''
    model = Outline
    template_name = 'fiction_outlines/outline_list.html'
    select_related = ['series']
    prefetch_related = ['arc_set', 'storyelementnode_set', 'characterinstance_set', 'locationinstance_set']
    context_object_name = 'outline_list'

    def get_queryset(self):
        return Outline.objects.filter(user=self.request.user)


class OutlineDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                        SelectRelatedMixin, PrefetchRelatedMixin, generic.DetailView):
    '''
    Generic view for Outline detail
    '''
    model = Outline
    template_name = 'fiction_outlines/outline_detail.html'
    permission_required = 'fiction_outlines.view_outline'
    select_related = ['series']
    prefetch_related = ['arc_set', 'characterinstance_set', 'locationinstance_set', 'storyelementnode_set']
    pk_url_kwarg = 'outline'
    context_object_name = 'outline'


class OutlineCreateView(LoginRequiredMixin, generic.CreateView):
    '''
    Generic view for creating initial outline.
    '''
    model = Outline
    template_name = 'fiction_outlines/outline_create.html'
    form_class = forms.OutlineForm
    success_url = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:outline_detail', kwargs={'outline': self.object.pk})

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class OutlineUpdateView(LoginRequiredMixin, PermissionRequiredMixin, generic.edit.UpdateView):
    '''
    Generic update view for outline details.
    '''
    model = Outline
    permission_required = 'fiction_outlines.edit_outline'
    template_name = 'fiction_outlines/outline_update.html'
    success_url = None
    form_class = forms.OutlineForm
    context_object_name = 'outline'
    pk_url_kwarg = 'outline'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:outline_detail', kwargs={'outline': self.object.pk})


class OutlineDeleteView(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    '''
    Generic delete view for an outline.
    '''
    model = Outline
    permission_required = 'fiction_outlines.delete_outline'
    template_name = 'fiction_outlines/outline_delete.html'
    success_url = reverse_lazy('fiction_outlines:outline_list')
    context_object_name = 'outline'
    pk_url_kwarg = 'outline'


class ArcListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    '''
    Generic list view for arcs in a outline
    '''
    model = Arc
    permission_required = 'fiction_outlines.view_outline'
    template_name = 'fiction_outlines/arc_list.html'
    context_object_name = 'arc_list'

    def dispatch(self, request, *args, **kwargs):
        self.outline = get_object_or_404(Outline, pk=kwargs['outline'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Arc.objects.filter(outline=self.outline).select_related(
            'outline').prefetch_related('arcelementnode_set')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['outline'] = self.outline
        return context

    def get_permission_object(self):
        return self.outline


class ArcDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                    SelectRelatedMixin, PrefetchRelatedMixin, generic.DetailView):
    '''
    Generic view for arc details.
    '''
    model = Arc
    permission_required = 'fiction_outlines.view_arc'
    template_name = 'fiction_outlines/arc_detail.html'
    select_related = ['outline']
    prefetch_related = ['arcelementnode_set']
    pk_url_kwarg = 'arc'
    context_object_name = 'arc'

    def dispatch(self, request, *args, **kwargs):
        self.outline = get_object_or_404(Outline, pk=kwargs['outline'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['annotated_list'] = ArcElementNode.get_annotated_list(parent=self.object.arc_root_node)
        return context


class ArcCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    '''
    Generic view for creating an arc.
    '''
    model = Arc
    permission_required = 'fiction_outlines.edit_outline'
    template_name = 'fiction_outlines/arc_create.html'
    fields = ['name', 'mace_type']
    success_url = None

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:arc_detail', kwargs={'outline': self.outline.pk, 'arc': self.object.pk})

    def dispatch(self, request, *args, **kwargs):
        self.outline = get_object_or_404(Outline, pk=kwargs['outline'])
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.outline

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['outline'] = self.outline
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = self.outline.create_arc(name=form.instance.name, mace_type=form.instance.mace_type)
                return HttpResponseRedirect(self.get_success_url())
        except IntegrityError as IE:
            form.add_error('name', str(IE))
            super().form_invalid(form)


class ArcUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SelectRelatedMixin, generic.edit.UpdateView):
    '''
    Generic view for updating arc details
    '''
    model = Arc
    permission_required = 'fiction_outlines.edit_arc'
    template_name = 'fiction_outlines/arc_update.html'
    success_url = None
    fields = ['name', 'mace_type']
    select_related = ['outline']
    pk_url_kwarg = 'arc'
    context_object_name = 'arc'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:arc_detail', kwargs={'arc': self.object.pk})


class ArcDeleteView(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    '''
    Generic view for deleting an arc
    '''
    model = Arc
    permission_required = 'fiction_outlines.delete_arc'
    template_name = 'fiction_outlines/arc_delete.html'
    success_url = None
    pk_url_kwarg = 'arc'
    context_object_name = 'arc'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:outline_detail', kwargs={'outline': self.outline.pk})

    def dispatch(self, request, *args, **kwargs):
        arc = get_object_or_404(Arc, pk=kwargs['arc'])
        self.outline = arc.outline
        return super().dispatch(request, *args, **kwargs)


# Now we start dealing with Element nodes for arc and story elements.
# Generic views are fine for some small edits on individual nodes, but
# actual tree mainipulation will need to be somewhat custom.


class ArcNodeDetailView(LoginRequiredMixin, PermissionRequiredMixin, SelectRelatedMixin,
                        PrefetchRelatedMixin, generic.DetailView):
    '''
    View for looking at the details of an atomic node as opposed to the whole tree.
    '''
    model = ArcElementNode
    permission_required = 'fiction_outlines.view_arc_node'
    template_name = 'fiction_outlines/arcnode_detail.html'
    pk_url_kwarg = 'arcnode'
    context_object_name = 'arcnode'
    select_related = ['arc', 'arc__outline', 'story_element_node']
    prefetch_related = ['assoc_characters', 'assoc_locations']


class ArcNodeCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    '''
    Create view for an arc node. Assumes that the target position has already been passed to it
    via kwargs.
    '''
    model = ArcElementNode
    permission_required = 'fiction_outlines.edit_arc'
    template_name = 'fiction_outlines/arcnode_create.html'
    form_class = forms.ArcNodeForm
    success_url = None

    def dispatch(self, request, *args, **kwargs):
        self.arc = get_object_or_404(Arc, pk=kwargs['arc'])
        self.target = get_object_or_404(ArcElementNode, pk=kwargs['arcnode'])
        self.pos = kwargs['pos']
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.arc

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['arc'] = self.arc
        return kwargs

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:arcnode_detail', kwargs={'outline': self.arc.outline.pk,
                                                                       'arc': self.arc.pk, 'arcnode': self.object.pk})

    def form_valid(self, form):
        if self.pos == 'addchild':
            try:
                with transaction.atomic():
                    self.object = self.target.add_child(description=form.instance.description,
                                                        arc_element_type=form.instance.arc_element_type,
                                                        story_element_node=form.instance.story_element_node,
                                                        assoc_characters=form.instance.assoc_characters,
                                                        assoc_locations=form.instance.assoc_locations)
            except NodeAlreadySaved:  # pragma: no cover
                # We don't care, as the record is already there.
                pass
            except ArcIntegrityError:
                form.add_error('arc_element_type', _("This would duplicate an existing milestone for this arc."))
        else:
            try:
                with transaction.atomic():
                    self.object = self.target.add_sibling(pos=self.pos, description=form.instance.description,
                                                          arc_element_type=form.instance.arc_element_type,
                                                          story_element_node=form.instance.story_element_node,
                                                          assoc_characters=form.instance.assoc_characters,
                                                          assoc_locations=form.instance.assoc_locations)
            except NodeAlreadySaved:  # pragma: no cover
                # We don't care as the record is already saved.
                pass
            except InvalidPosition as IP:
                form.add_error('description', _("You are trying to put this into an invalid position."))
                logger.error(str(IP))
                return super().form_invalid(form)
            except IntegrityError as IE:
                form.add_error('description', str(IE))
                return super().form_invalid(form)
            except ArcIntegrityError:
                form.add_error('arc_element_type', _("This would duplicate an existing milestone for this arc."))
                return super().form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())


class ArcNodeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SelectRelatedMixin,
                        PrefetchRelatedMixin, generic.edit.UpdateView):
    '''
    View for editing details of an arc node (but not it's tree position).
    '''
    model = ArcElementNode
    permission_required = 'fiction_outlines.edit_arc_node'
    template_name = 'fiction_outlines/arcnode_update.html'
    pk_url_kwarg = 'arcnode'
    context_object_name = 'arcnode'
    select_related = ['arc', 'arc__outline', 'story_element_node']
    prefetch_related = ['assoc_characters', 'assoc_locations']
    form_class = forms.ArcNodeForm
    success_url = None

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['arc'] = self.object.arc
        return kwargs

    def form_valid(self, form):
        try:
            tree_manipulation.send(sender=ArcElementNode, instance=form.instance,
                                   action='update', target_node=None,
                                   target_node_type=form.instance.arc_element_type, pos=None)
        except ArcIntegrityError as AE:
            form.add_error('arc_element_type', str(AE))
            return super().form_invalid(form)
        return super().form_valid(form)


class ArcNodeMoveView(LoginRequiredMixin, PermissionRequiredMixin, generic.edit.UpdateView):
    '''
    View for executing a move method on an arcnode.
    '''
    model = ArcElementNode
    permission_required = 'fiction_outlines.edit_arc_node'
    pk_url_kwarg = 'arcnode'
    context_object_name = 'arcnode'
    form_class = movenodeform_factory(ArcElementNode, form=forms.OutlineMoveNodeForm, exclude=(
        'headline',
        'id',
        'description',
        'assoc_characters',
        'assoc_locations',
        'story_element_node',
        'arc_element_type',
        'arc'))
    success_url = None
    template_name = 'fiction_outlines/arcnode_move.html'

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        url = self.object.get_absolute_url()
        logger.debug("Found success url of %s" % url)
        return url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['root_node'] = self.object.get_root()
        logger.debug('For object %s (%s, %s), found root node of %s (%s, %s)' % (
            self.object.pk,
            self.object.arc.name,
            self.object.arc_element_type,
            kwargs['root_node'].pk,
            kwargs['root_node'].arc.name,
            kwargs['root_node'].arc_element_type
        ))
        return kwargs

    def form_valid(self, form):
        logger.debug("Attepting move within an atomic transaction...")
        try:
            with transaction.atomic():
                self.object = form.save()
        except InvalidPosition as IP:
            form.add_error('_position', _("This is not a permitted position"))
            logger.error(_('This is not a permitted position. \n Details: %s' % str(IP)))
            return self.form_invalid(form)
        except InvalidMoveToDescendant as IMD:
            form.add_error('_position', _("You cannot move an item to be a sibling or child of its own descendant."))
            logger.debug(_("You cannot move item to be a sibling or child of own descendant. Details: %s" % str(IMD)))
            return self.form_invalid(form)
        except PathOverflow as PO:
            form.add_error('_position', _('Apologies, there has been a database error. This has been logged.'))
            logger.error(str(PO))
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())


class ArcNodeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SelectRelatedMixin,
                        PrefetchRelatedMixin, generic.edit.DeleteView):
    '''
    View for deleting an arc node.
    '''
    model = ArcElementNode
    permission_required = 'fiction_outlines.delete_arc_node'
    template_name = 'fiction_outlines/arcnode_delete.html'
    pk_url_kwarg = 'arcnode'
    context_object_name = 'arcnode'
    select_related = ['arc', 'arc__outline', 'story_element_node']
    prefetch_related = ['assoc_characters', 'assoc_locations']
    success_url = None

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:arc_detail',
                            kwargs={'outline': self.outline.pk, 'arc': self.arc.pk})

    def dispatch(self, request, *args, **kwargs):
        self.outline = get_object_or_404(Outline, pk=kwargs['outline'])
        self.arc = get_object_or_404(Arc, pk=kwargs['arc'])
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.arc_element_type in ['mile_hook', 'mile_reso']:
            return render(self.request, self.template_name, context=self.get_context_data(), content_type='text/html')
        return super().delete(request, *args, **kwargs)


class StoryNodeDetailView(LoginRequiredMixin, PermissionRequiredMixin, SelectRelatedMixin,
                          PrefetchRelatedMixin, generic.DetailView):
    '''
    View for looking at the details of an atomic story node as opposed to the whole tree.
    '''
    model = StoryElementNode
    permission_required = 'fiction_outlines.view_story_node'
    template_name = 'fiction_outlines/storynode_detail.html'
    pk_url_kwarg = 'storynode'
    context_object_name = 'storynode'
    select_related = ['outline']
    prefetch_related = ['arcelementnode_set', 'assoc_characters', 'assoc_locations']


class StoryNodeCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    '''
    Creation view for a story node. Assumes the target and pos have been passed as kwargs.
    '''
    model = StoryElementNode
    permission_required = 'fiction_outlines.edit_outline'
    template_name = 'fiction_outlines/storynode_create.html'
    form_class = forms.StoryNodeForm
    success_url = None

    def dispatch(self, request, *args, **kwargs):
        self.outline = get_object_or_404(Outline, pk=kwargs['outline'])
        self.target = get_object_or_404(StoryElementNode, pk=kwargs['storynode'])
        self.pos = kwargs['pos']
        return super().dispatch(request, *args, **kwargs)

    def get_permission_object(self):
        return self.outline

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:storynode_detail', kwargs={'outline': self.outline.pk,
                                                                         'storynode': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['outline'] = self.outline
        return kwargs

    def form_valid(self, form):
        if self.pos == 'addchild':
            try:
                with transaction.atomic():
                    self.object = self.target.add_child(story_element_type=form.instance.story_element_type,
                                                        name=form.instance.name,
                                                        description=form.instance.description)
                    if form.instance.assoc_characters:
                        self.object.assoc_characters.set(form.instance.assoc_characters.all())
                    if form.instance.assoc_locations:
                        self.object.assoc_locations.set(form.instance.assoc_locations.all())

            except NodeAlreadySaved:  # pragma: no cover
                # We don't care since it means the record got saved for us already.
                pass
            except IntegrityError as IE:
                form.add_error('story_element_type', str(IE))
                return super().form_invalid(form)
        else:
            try:
                with transaction.atomic():
                    self.object = self.target.add_sibling(pos=self.pos,
                                                          story_element_type=form.instance.story_element_type,
                                                          name=form.instance.name,
                                                          description=form.instance.description)
                    if form.instance.assoc_characters:
                        self.object.assoc_characters.set(form.instance.assoc_characters.all())
                    if form.instance.assoc_locations:
                        self.object.assoc_locations.set(form.instance.assoc_locations.all())

            except NodeAlreadySaved:  # pragma: no cover
                # We don't care since we already got what we wanted.
                pass
            except InvalidPosition as IP:
                logger.error(str(IP))
                form.add_error('description', _("This item cannot be placed into this position."))
                return super().form_invalid(form)
            except IntegrityError as IE:
                form.add_error('story_element_type', str(IE))
                logger.error(str(IE))
                return super().form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())


class StoryNodeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SelectRelatedMixin,
                          PrefetchRelatedMixin, generic.edit.UpdateView):
    '''
    View for doing basic updates to a story node, but not regarding its position in the tree.
    '''
    model = StoryElementNode
    permission_required = 'fiction_outlines.edit_story_node'
    template_name = 'fiction_outlines/storynode_update.html'
    pk_url_kwarg = 'storynode'
    context_object_name = 'storynode'
    select_related = ['outline']
    prefetch_related = ['arcelementnode_set', 'assoc_characters', 'assoc_locations']
    form_class = forms.StoryNodeForm
    success_url = None

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:storynode_update', kwargs={'outline': self.object.outline.pk,
                                                                         'storynode': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['outline'] = self.object.outline
        return kwargs

    def form_valid(self, form):
        try:
            tree_manipulation.send(sender=StoryElementNode, instance=form.instance, action='update',
                                   target_node_type=form.instance.story_element_type, target_node=None, pos=None)
        except IntegrityError as IE:
            form.add_error('story_element_type', str(IE))
            return self.form_invalid(form)
        return super().form_valid(form)


class StoryNodeMoveView(StoryNodeUpdateView):
    '''
    View for executing a move method on an arcnode.
    '''

    form_class = movenodeform_factory(StoryElementNode, form=forms.OutlineMoveNodeForm, exclude=(
        'name',
        'id',
        'description',
        'assoc_characters',
        'assoc_locations',
        'outline',
        'story_element_type'
    ))
    success_url = None
    template_name = 'fiction_outlines/storynode_move.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        del kwargs['outline']
        kwargs['root_node'] = self.object.get_root()
        return kwargs

    def form_valid(self, form):
        try:
            ref_node = get_object_or_404(StoryElementNode, pk=form.cleaned_data['_ref_node_id'])
            tree_manipulation.send(sender=StoryElementNode, instance=form.instance, action='move',
                                   target_node_type=ref_node.story_element_type,
                                   target_node=ref_node, pos=form.cleaned_data['_position'])
        except IntegrityError as IE:
            form.add_error('_ref_node_id', str(IE))
            return self.form_invalid(form)
        try:
            with transaction.atomic():
                form.save()
        except InvalidPosition as IP:
            form.add_error('_position', _("This is not a permitted position"))
            return self.form_invalid(form)
        except InvalidMoveToDescendant as IMD:
            form.add_error('_position', _("You cannot move an item to be a sibling or child of its own descendant."))
            return self.form_invalid(form)
        except PathOverflow as PO:
            form.add_error('_position', _('Apologies, there has been a database error. This has been logged.'))
            logger.error(str(PO))
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())


class StoryNodeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SelectRelatedMixin,
                          PrefetchRelatedMixin, generic.edit.DeleteView):
    '''
    Genric view for deleting a story node.
    '''
    model = StoryElementNode
    permission_required = 'fiction_outlines.delete_story_node'
    template_name = 'fiction_outlines/storynode_delete.html'
    pk_url_kwarg = 'storynode'
    context_object_name = 'storynode'
    select_related = ['outline']
    prefetch_related = ['arcelementnode_set', 'assoc_characters', 'assoc_locations']
    success_url = None

    def get_success_url(self):
        if self.success_url:
            return self.success_url  # pragma: no cover
        return reverse_lazy('fiction_outlines:outline_detail', kwargs={'outline': self.outline.pk})

    def dispatch(self, request, *args, **kwargs):
        self.outline = get_object_or_404(Outline, pk=kwargs['outline'])
        return super().dispatch(request, *args, **kwargs)
