"""
Signal handlers for discussions events
"""
import logging
from uuid import uuid4

from django.db import transaction

from openedx.core.djangoapps.discussions.data import CourseDiscussionConfigurationData
from openedx.core.djangoapps.discussions.models import (
    DEFAULT_PROVIDER_TYPE,
    DiscussionTopicLink,
    DiscussionsConfiguration,
)
from openedx.core.djangoapps.discussions.signals import COURSE_DISCUSSIONS_UPDATED

log = logging.getLogger(__name__)


# pylint: disable=unused-argument
def handle_course_discussion_config_update(sender, configuration: CourseDiscussionConfigurationData, **kwargs):
    """
    Updates the database models for course topics and configuration when settings are updated in the course.

    Args:
        sender: Ignored
        configuration (CourseDiscussionConfigurationData): configuration data for the course

    """
    update_course_discussion_config(configuration)


def update_course_discussion_config(configuration: CourseDiscussionConfigurationData):
    """
    Update the database version of the configuration if it changes in the course structure.

    This function accepts a discussion configuration object that represents the current
    configuration and applies that state to the database. It will go over the list of topic
    links in the configuration, find the corresponding topic link in the database and apply
    any changes if needed. If a new topic link has been introduced it will create an entry.
    If a topic has been removed, it will deactivate the entry.

    When this runs on a new course it will create a new DiscussionConfiguration entry for
    the course.

    Args:
        configuration (CourseDiscussionConfigurationData): configuration data for the course
    """
    course_key = configuration.course_key
    provider_id = configuration.provider_type or DEFAULT_PROVIDER_TYPE
    new_topic_map = {
        (topic_context.usage_key or topic_context.external_id): topic_context
        for topic_context in configuration.contexts
    }
    with transaction.atomic():
        log.info(f"Updating existing discussion topic links for {course_key}")
        for topic_link in DiscussionTopicLink.objects.filter(
            context_key=course_key, provider_id=provider_id,
        ):
            lookup_key = topic_link.usage_key or topic_link.external_id
            topic_context = new_topic_map.pop(lookup_key, None)
            # TODO: handle deleting topics that are no longer in use
            # currently this will simply not work for course-wide topics since deleting the link will
            # remove access to all posts in the topic.
            if topic_context is None:
                topic_link.enabled_in_context = False
            else:
                topic_link.enabled_in_context = True
                topic_link.title = topic_context.title
            topic_link.save()
        log.info(f"Creating new discussion topic links for {course_key}")

        DiscussionTopicLink.objects.bulk_create([
            DiscussionTopicLink(
                context_key=course_key,
                usage_key=topic_context.usage_key,
                title=topic_context.title,
                provider_id=provider_id,
                external_id=topic_context.external_id or uuid4(),
                enabled_in_context=True,
            )
            for topic_context in new_topic_map.values()
        ])

        if not DiscussionsConfiguration.objects.filter(context_key=course_key).exists():
            log.info(f"Course {course_key} doesn't have discussion configuration model yet. Creating a new one.")
            DiscussionsConfiguration(
                context_key=course_key,
                provider_type=provider_id,
                plugin_configuration=configuration.plugin_configuration,
                enable_in_context=configuration.enable_in_context,
                enable_graded_units=configuration.enable_graded_units,
                unit_level_visibility=configuration.unit_level_visibility,
            ).save()


COURSE_DISCUSSIONS_UPDATED.connect(handle_course_discussion_config_update)
