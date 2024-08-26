from flask import Blueprint, request, jsonify
from bioxpress.services.stats_service import get_stats
from bioxpress.services.cancer_service import search_cancer, get_cancer_list

api_bp = Blueprint("api", __name__)


@api_bp.route("/stats", methods=["POST"])
def stats():
    json_data = request.get_json()
    result = get_stats(json_data)
    return jsonify(result)


@api_bp.route("/search_cancer", methods=["POST"])
def search_cancer_route():
    input_json = request.get_json()
    result = search_cancer(input_json)
    return jsonify(result)


@api_bp.route("/get_cancer_list", methods=["GET"])
def get_cancer_list_route():
    result = get_cancer_list()
    return jsonify(result)
