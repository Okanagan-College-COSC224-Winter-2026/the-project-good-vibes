"""
Practice endpoint for lab assignment
"""

from flask import Blueprint, jsonify

practice = Blueprint("practice", __name__, url_prefix="/practice")


@practice.route("/test", methods=["GET"])
def practice_test():
    """
    Practice endpoint that returns course information
    """
    return jsonify({"course": "cosc 224"}), 200
