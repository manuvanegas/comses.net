"""
Initializes Wagtail Page Models and other canned data. 
FIXME: move logic to dedicated module if this gets too unwieldy
"""

import logging

from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site as DjangoSite
from django.core.management.base import BaseCommand
from django.urls import reverse
from wagtail.wagtailcore.models import Page, Site

from drupal_migrator.database_migration import load_licenses, load_platforms, load_journals
from home.models import (LandingPage, FeaturedContentItem, SocialMediaSettings,
                         PlatformsIndexPage, Platform, PlatformSnippetPlacement, CategoryIndexPage, StreamPage,
                         JournalsIndexPage, JournalSnippetPlacement, Journal)
from library.models import Codebase

logger = logging.getLogger(__name__)



class ResourceSection():

    SUBNAVIGATION_LINKS = (
            ('Resources', '/resources/'),
            ('Modeling Platforms', 'modeling-platforms/'),
            ('Journals', 'journals/'),
            ('Standards', 'standards/'),
    )

    def __init__(self, root_page, default_user):
        self.root_page = root_page
        self.default_user = default_user

    def build_resource_index(self):
        resources_index = CategoryIndexPage(
            heading='Resources',
            title='CoMSES Net Resources',
            slug='resources',
            summary=('CoMSES Net is dedicated to fostering open and reproducible computational modeling through '
                     'cyberinfrastructure and community development. We maintain these community curated resources '
                     'to help new and experienced computational modelers improve the discoverability, reuse, and '
                     'reproducibility of their computational models. Please [contact us](/contact/) with '
                     'feedback or additional resources - your contributions are appreciated!'
                     )
        )
        # FIXME: replace with wagtailmenus FlatMenu creation and associated with the resources_index
        resources_index.add_breadcrumbs(self.SUBNAVIGATION_LINKS[:1])
        resources_index.add_navigation_links(self.SUBNAVIGATION_LINKS)
        resources_index.add_callout(
            image_path='core/static/images/icons/modeling-platforms.png',
            title='Modeling Platforms',
            url='modeling-platforms/',
            user=self.default_user,
            sort_order=1,
            caption=('Preserve the complete digital pipeline used to derive a publishable finding. Other researchers '
                     'will be able to discover, cite, and run your code in a reproducible containerized environment.')
        )
        resources_index.add_callout(
            image_path='core/static/images/icons/journals.png',
            title='Scholarly Journals',
            url='journals/',
            caption=('A community curated list of scholarly journals covering a wide range methodological and '
                     'theoretical concerns for agent-based other types of computational modeling.'),
            user=self.default_user,
            sort_order=1,
        )
        resources_index.add_callout(
            image_path='core/static/images/icons/standards.png',
            title='Documentation Standards',
            url='standards/',
            caption=(
            'Advancing the use of agent-based models in scholarly research demands rigorous standards in model '
            'and experiment documentation. Volker Grimm et al. have developed a protocol for describing '
            'agent-based and individual-based models called '
            '[ODD (Overview, Design Concepts, and Details)](https://doi.org/10.1016/j.ecolmodel.2010.08.019) '
            '"designed to ensure that such descriptions are readable and complete."'
            ),
            user=self.default_user,
            sort_order=2,
        )
        resources_index.add_callout(
            image_path='core/static/images/icons/educational-materials.png',
            title='Educational Materials',
            url='educational-materials/',
            caption=('Tutorials, websites, books, and classroom / course materials on agent-based modeling that cover '
                     'various modeling platforms (e.g., RePast, NetLogo, Mason, FLAME).'),
            user=self.default_user,
            sort_order=3,
        )
        resources_index.add_callout(
            image_path='core/static/images/icons/guides-to-good-practice.png',
            title='Guides to Good Practice',
            url='guides-to-good-practice/',
            caption=('Good practices for agent-based modeling as inspired by '
                     '[this Software Carpentry paper](https://swcarpentry.github.io/good-enough-practices-in-scientific-computing/)'),
            user=self.default_user,
            sort_order=4,
        )
        resources_index.add_callout(
            image_path='core/static/images/icons/events.png',
            url=reverse('home:event-list'),
            title='Find Upcoming Events',
            caption=('Find calls for papers and participation in upcoming conferences, workshops, and other events '
                     'curated by the CoMSES Net Community.'),
            user=self.default_user,
            sort_order=5,
        )
        self.root_page.add_child(instance=resources_index)
        return resources_index

    def build_platforms_index(self, parent_page):
        platforms_index_page = PlatformsIndexPage(
            title='Computational Modeling Platforms',
            slug='modeling-platforms',
            description=("Computational modeling platforms provide a wide range of modeling strategies, scaffolding, "
                         "and support for developers of agent-based models. Please [let us know](/contact/) if you "
                         "have any corrections or would like to submit a new platform.")
        )
        platforms_index_page.add_breadcrumbs(self.SUBNAVIGATION_LINKS[:2])
        platforms_index_page.add_navigation_links(self.SUBNAVIGATION_LINKS)
        for idx, platform in enumerate(Platform.objects.exclude(name='other').order_by('name')):
            platforms_index_page.platform_placements.add(
                PlatformSnippetPlacement(sort_order=idx, platform=platform)
            )
        parent_page.add_child(instance=platforms_index_page)

    def build_journal_page(self, parent):
        journal_page = JournalsIndexPage(
            title='Computational Modeling Journals',
            description=('An list of scholarly journals that address theoretical and methodological concerns for '
                         'agent-based modeling and related computational modeling sciences.'),
        )
        # FIXME: arcane step value slice to pick out Resources -> Journals
        journal_page.add_breadcrumbs(self.SUBNAVIGATION_LINKS[0:3:2])
        journal_page.add_navigation_links(self.SUBNAVIGATION_LINKS)

        for idx, journal in enumerate(Journal.objects.order_by('name')):
            journal_page.journal_placements.add(
                JournalSnippetPlacement(sort_order=idx, journal=journal)
            )
        parent.add_child(instance=journal_page)

    def build_standards_page(self, parent):
        pass

    def build(self):
        resources_index = self.build_resource_index()
        self.build_platforms_index(resources_index)
        self.build_journal_page(resources_index)
        self.build_standards_page(resources_index)


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site = None
        self.landing_page = None
        self.default_user = User.objects.get(username='alee')

    def add_arguments(self, parser):
        parser.add_argument('--site-name',
                            default='CoMSES Net',
                            help='Site human readable name, e.g., Network for Computational ...')
        parser.add_argument('--site-domain',
                            default='www.comses.net',
                            help='Site domain name, e.g., www.comses.net')
        parser.add_argument('--reload-platforms', default=False, action='store_true')
        parser.add_argument('--reload-licenses', default=False, action='store_true')

    def handle(self, *args, **options):
        if options['reload_platforms']:
            load_platforms()
        if options['reload_licenses']:
            load_licenses()
        if options['reload_journals']:
            load_journals()

        self.create_landing_page()
        # argparse converts dashes to underscores
        self.create_site(site_name=options['site_name'], hostname=options['site_domain'])
        self.create_social_apps()
        # create community, about, resources pages
        self.create_community_section()
        ResourceSection(self.landing_page, self.default_user).build()
        self.create_about_section()

    @staticmethod
    def create_social_apps():
        site = DjangoSite.objects.first()
        if SocialApp.objects.count() == 0:
            orcid_app, created = SocialApp.objects.get_or_create(
                provider='orcid',
                name='ORCID',
                client_id=settings.ORCID_CLIENT_ID,
                secret=settings.ORCID_CLIENT_SECRET,
            )
            orcid_app.sites.add(site)
            github_app, created = SocialApp.objects.get_or_create(
                provider='github',
                name='GitHub',
                client_id=settings.GITHUB_CLIENT_ID,
                secret=settings.GITHUB_CLIENT_SECRET,
            )
            github_app.sites.add(site)

    def create_site(self, site_name, hostname):
        site = Site.objects.first() if Site.objects.count() > 0 else Site()
        site.site_name = site_name
        site.hostname = hostname
        site.is_default_site = True
        site.root_page = self.landing_page
        site.save()
        sms = SocialMediaSettings.for_site(site)
        sms.youtube_url = 'https://www.youtube.com/user/CoMSESNet/'
        sms.twitter_account = 'openabm_comses'
        sms.mailing_list_url = 'http://eepurl.com/b8GCUv'
        sms.save()
        self.site = site

    def create_landing_page(self):
        root_page = Page.objects.get(path='0001')
        # delete root page's initial children.
        root_page.get_children().delete()
        LandingPage.objects.delete()
        landing_page = LandingPage(
            title='CoMSES Net Home Page',
            slug='home',
            mission_statement=('CoMSES Net is an international network of researchers, educators and professionals '
                               'with the common goal of improving the way we develop, share, and use agent based '
                               'modeling in the social and ecological sciences.'
                               ),
        )
        for codebase in Codebase.objects.peer_reviewed():
            # if there are multiple images, just pull the first
            fc_dict = codebase.as_featured_content_dict()
            if fc_dict['image']:
                landing_page.featured_content_queue.add(FeaturedContentItem(**fc_dict))
        # refresh from DB before adding more nodes so treebeard can clean up its internals
        # https://django-treebeard.readthedocs.io/en/latest/caveats.html
        root_page.refresh_from_db()
        root_page.add_child(instance=landing_page)
        self.landing_page = landing_page


    def create_community_section(self):
        community_index = CategoryIndexPage(
            heading='Community',
            title='Welcome to the CoMSES Net Community',
            slug='community',
            summary=('CoMSES Net is dedicated to fostering open and reproducible scientific computation through '
                     'cyberinfrastructure and community development. We curate [resources for '
                     'model-based science](/resources/) including tutorials and FAQs on agent-based modeling, a '
                     '[computational model library](/codebases/) to help researchers archive their work and discover '
                     'and reuse other&apos;s works, and '
                     '[forums for discussions, job postings, and events.](https://forum.comses.net)'
                     ),
        )
        community_index.add_breadcrumbs([
            ('Community', '/community/')
        ])
        community_index.add_navigation_links([
            ('Community', '/community/'),
            ('Forum', settings.DISCOURSE_BASE_URL),
            ('Users', reverse('home:profile-list')),
            ('Jobs', reverse('home:job-list')),
        ])
        # add callouts
        community_index.add_callout(
            image_path='core/static/images/icons/connect.png',
            title='Connect with Researchers',
            url=reverse('home:profile-list'),
            user=self.default_user,
            sort_order=1,
            caption=('Follow other researchers, their models, or other topics of interest. Engage in discussions, '
                     'participate in upcoming events, or find a new job. Preserve the complete digital pipeline used to '
                     'derive a publishable finding. Other researchers will be able to discover, cite, and run your code '
                     'in a reproducible' 'containerized environment.')
        )

        community_index.add_callout(
            image_path='core/static/images/icons/events.png',
            title='Find Upcoming Events',
            url=reverse('home:event-list'),
            user=self.default_user,
            sort_order=2,
            caption=('Find calls for papers and participation in upcoming conferences, workshops, and other events '
                     'curated by the CoMSES Net Community.'),
        )

        community_index.add_callout(
            image_path='core/static/images/icons/jobs.png',
            title='Search Jobs & Appointments',
            url=reverse('home:job-list'),
            user=self.default_user,
            sort_order=3,
            caption=('We maintain an open job board with academic and industry positions relevant to the CoMSES Net '
                     'Community. Any CoMSES Net Member can register and post positions here.')
        )
        self.landing_page.add_child(instance=community_index)

    def create_about_section(self):
        about_index = CategoryIndexPage(
            heading='About',
            title='About CoMSES Net / OpenABM',
            slug='about',
            summary=('Welcome! CoMSES Net, the Network for Computational Modeling in Social and Ecological Sciences, '
                     'is an open community of researchers, educators, and professionals with a common goal - improving '
                     'the way we develop, share, use, and re-use agent based and computational models for the study of '
                     'social and ecological systems. We have been developing a computational model library to preserve '
                    'the digital artifacts and source code that comprise an agent based model and encourage you to '
                     'register and [add your models to the archive](/codebases/create/). We are governed by an '
                     'international board and ex-officio members (PIs of the projects that fund CoMSES Net) and '
                     'operate under [these by-laws](/about/by-laws).'
                     ),
        )
        about_index.add_breadcrumbs([('About CoMSES Net', '/about/')])
        about_index.add_navigation_links([('Overview', '/about/'),
                                          ('People', 'people/'),
                                          ('FAQs', '/faq/'),
                                          ('Contact', '/contact/')])
        about_index.add_callout(
            image_path='core/static/images/icons/digital-archive.png',
            title='Provide trusted digital preservation and curation',
            user=self.default_user,
            sort_order=1,
            caption='Facilitate reuse and reproducibility with rich contextual metadata.'
        )
        about_index.add_callout(
            image_path='core/static/images/icons/culture.png',
            title='Promote a culture of sharing',
            user=self.default_user,
            sort_order=2,
            caption='Publish or perish. Share or shrivel.',
        )
        about_index.add_callout(
            image_path='core/static/images/icons/cog.png',
            title='Improve theoretical and methodological practice',
            user=self.default_user,
            sort_order=3,
            caption='''Engage with practitioners to address theoretical concerns and improve methodological practices 
            for reuse and reusability.''',
        )
        self.landing_page.add_child(instance=about_index)
        people_page = StreamPage(
            title='People',
            description=("The CoMSES Net Directorate is led by Michael Barton, Marco Janssen, Allen Lee, and Lilian "
                         "Na'ia Alessa. It also includes an executive board elected by full CoMSES Net members and a "
                         "support staff with expertise in digital curation and cyberinfrastructure development."
                         ),
        )
        about_index.add_child(instance=people_page)
