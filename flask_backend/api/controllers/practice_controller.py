"""
Fake API endpoints for testing/development
"""

from flask import Blueprint, jsonify, request

practice = Blueprint("practice", __name__, url_prefix="/practice")


@practice.route("/test", methods=("GET",))
def get_test():
    if request.method == "GET":
        return (
            jsonify(
               
                    {
                        'course': 'cosc 224',
                    }

            ),
            200,
        )