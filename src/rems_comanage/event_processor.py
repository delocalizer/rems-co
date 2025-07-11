#!/usr/bin/env python3
"""
REMS Event Notification Server

A lightweight web server that receives JSON event notifications from REMS
and processes them to take actions in COManage.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from flask import Flask, request, jsonify
import requests

# Import the COManage client
sys.path.append("/home/conrad/git/rems-comanage/src")
from rems_comanage.comanage_client import COManageClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("rems_event_server.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class REMSEventProcessor:
    """Processes REMS events and triggers COManage actions"""

    def __init__(
        self, comanage_client: COManageClient, resource_group_mapping: Dict[str, str]
    ):
        self.comanage_client = comanage_client
        self.resource_group_mapping = resource_group_mapping

    #    def create_entitlement_update_payload(entitlement: Dict[str, Any], group_id: str, person_id: str) -> Dict[str, Any]:
    #        """
    #        Converts an entitlement to a CoManage group request payload.
    #
    #        Args:
    #            entitlement: The entitlement data
    #            group_id: CoManage group ID
    #            person_id: CoManage person ID
    #
    #        Returns:
    #            JSON payload for CoManage API
    #        """
    #        return {
    #            "RequestType": "CoGroupMembers",
    #            "Version": "1.0",
    #            "CoGroupMembers": [{
    #                "Version": "1.0",
    #                "CoGroupId": group_id,
    #                "Person": {
    #                    "Type": "CO",
    #                    "Id": person_id
    #                },
    #                "Member": True,
    #                "Owner": False
    #            }]
    #        }
    #
    #
    #    def process_entitlement_add(comanage_client, entitlement: Dict[str, Any]) -> Dict[str, Any]:
    #        """
    #        Process an entitlement addition by calling the correct CoManage API method.
    #
    #        Args:
    #            comanage_client: CoManage client instance
    #            entitlement: Entitlement data containing 'resid' and 'userid'
    #
    #        Returns:
    #            Response from CoManage API
    #        """
    #        # Get the group and person IDs from CoManage
    #        group_id = comanage_client.get_group_id(entitlement['resid'])
    #        person_id = comanage_client.get_person_id(entitlement['userid'])
    #
    #        # Create the payload
    #        payload = create_entitlement_update_payload(entitlement, group_id, person_id)
    #
    #        # Call the correct method
    #        return comanage_client.create_or_update_permissions(payload)
    #
    #
    #    def process_entitlement_remove(comanage_client, entitlement: Dict[str, Any]) -> Dict[str, Any]:
    #        """
    #        Process an entitlement removal by calling the CoManage delete method.
    #
    #        Args:
    #            comanage_client: CoManage client instance
    #            entitlement: Entitlement data containing 'resid' and 'userid'
    #
    #        Returns:
    #            Response from CoManage API
    #        """
    #        # Get the group and person IDs from CoManage
    #        group_id = comanage_client.get_group_id(entitlement['resid'])
    #        person_id = comanage_client.get_person_id(entitlement['userid'])
    #
    #        # Get the group member ID and delete
    #        group_member_id = comanage_client.get_group_member_id(group_id, person_id)
    #        return comanage_client.delete_permissions(group_member_id)

    def process_approved_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Process an application.event/approved event

        Args:
            event_data: The complete event data from REMS

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        try:
            # Extract key information
            event_id = event_data.get("event/id")
            application_id = event_data.get("application/id")
            actor = event_data.get("event/actor")

            logger.info(
                f"Processing approved event {event_id} for application {application_id}"
            )

            # Get application data
            application = event_data.get("event/application")
            if not application:
                logger.error(f"No application data found in event {event_id}")
                return False

            # Get users to add (applicant + members)
            users_to_add = self._extract_users_from_application(application)
            if not users_to_add:
                logger.warning(f"No users found in application {application_id}")
                return True

            # Get resources and map to COManage groups
            resources = application.get("application/resources", [])
            groups_to_add = self._map_resources_to_groups(resources)

            if not groups_to_add:
                logger.warning(
                    f"No COManage groups mapped for resources in application {application_id}"
                )
                return True

            # Add users to groups
            success = self._add_users_to_groups(
                users_to_add, groups_to_add, application_id
            )

            if success:
                logger.info(f"Successfully processed approved event {event_id}")
            else:
                logger.error(f"Failed to process approved event {event_id}")

            return success

        except Exception as e:
            logger.error(f"Error processing approved event: {str(e)}")
            return False

    def _extract_users_from_application(self, application: Dict[str, Any]) -> List[str]:
        """Extract all users (applicant + members) from the application"""
        users = []

        # Add applicant
        applicant = application.get("application/applicant", {})
        if applicant and "userid" in applicant:
            users.append(applicant["userid"])

        # Add members
        members = application.get("application/members", [])
        for member in members:
            if "userid" in member:
                users.append(member["userid"])

        return users

    def _map_resources_to_groups(self, resources: List[Dict[str, Any]]) -> List[str]:
        """Map REMS resources to COManage groups"""
        groups = []

        for resource in resources:
            resource_ext_id = resource.get("resource/ext-id")
            if resource_ext_id and resource_ext_id in self.resource_group_mapping:
                group_id = self.resource_group_mapping[resource_ext_id]
                groups.append(group_id)
                logger.info(f"Mapped resource {resource_ext_id} to group {group_id}")
            else:
                logger.warning(f"No group mapping found for resource {resource_ext_id}")

        return groups

    def _add_users_to_groups(
        self, users: List[str], groups: List[str], application_id: int
    ) -> bool:
        """Add users to COManage groups"""
        success = True

        for user_id in users:
            for group_id in groups:
                try:
                    # Translate REMS user ID to COManage user ID if needed
                    comanage_user_id = self._translate_user_id(user_id)

                    # Add user to group using COManage client
                    result = self.comanage_client.add_user_to_group(
                        comanage_user_id, group_id
                    )

                    if result:
                        logger.info(
                            f"Added user {user_id} to group {group_id} for application {application_id}"
                        )
                    else:
                        logger.error(
                            f"Failed to add user {user_id} to group {group_id} for application {application_id}"
                        )
                        success = False

                except Exception as e:
                    logger.error(
                        f"Error adding user {user_id} to group {group_id}: {str(e)}"
                    )
                    success = False

        return success

    def _translate_user_id(self, rems_user_id: str) -> str:
        """
        Translate REMS user ID to COManage user ID

        This is a placeholder - implement based on your ID mapping strategy
        """
        # For now, assume they're the same
        return rems_user_id


# Configuration
RESOURCE_GROUP_MAPPING = {
    # Example mapping - replace with your actual resource -> group mappings
    "urn:nbn:fi:lb-201403262": "sensitive-data-group",
    "Extra Data": "extra-data-group",
    # Add more mappings as needed
}

# Initialize COManage client
# TODO: Replace with actual COManage client initialization
comanage_client = COManageClient()  # Add required parameters

# Initialize event processor
event_processor = REMSEventProcessor(comanage_client, RESOURCE_GROUP_MAPPING)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/rems-events", methods=["PUT"])
def receive_rems_event():
    """
    Receive REMS event notifications

    REMS sends events via HTTP PUT as described in the documentation
    """
    try:
        # Parse JSON data
        event_data = request.get_json()

        if not event_data:
            logger.warning("Received empty or invalid JSON data")
            return jsonify({"error": "Invalid JSON data"}), 400

        # Log the event
        event_type = event_data.get("event/type")
        event_id = event_data.get("event/id")
        application_id = event_data.get("application/id")

        logger.info(
            f"Received event: {event_type} (ID: {event_id}, App: {application_id})"
        )

        # Process the event based on type
        if event_type == "application.event/approved":
            success = event_processor.process_approved_event(event_data)

            if success:
                logger.info(f"Successfully processed event {event_id}")
                return "OK", 200
            else:
                logger.error(f"Failed to process event {event_id}")
                # Still return 200 to prevent retries for processing errors
                return "OK", 200

        else:
            # For now, just log other event types
            logger.info(f"Received unhandled event type: {event_type}")
            return "OK", 200

    except Exception as e:
        logger.error(f"Error processing REMS event: {str(e)}")
        # Return 200 to prevent retries - log the error for investigation
        return "OK", 200


@app.route("/rems-events", methods=["GET"])
def get_endpoint_info():
    """Provide information about the endpoint"""
    return jsonify(
        {
            "endpoint": "/rems-events",
            "method": "PUT",
            "description": "Receives REMS event notifications",
            "supported_events": ["application.event/approved"],
        }
    )


if __name__ == "__main__":
    logger.info("Starting REMS Event Notification Server")

    # Run the server
    app.run(
        host="0.0.0.0",  # Listen on all interfaces
        port=5000,  # Default port - change as needed
        debug=False,  # Set to True for development
    )
