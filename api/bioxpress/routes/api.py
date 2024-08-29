from flask import Blueprint, request, jsonify
from bioxpress.services.stats_service import get_stats
from bioxpress.services.transcript_service import get_transcript_data, transcript_search
from bioxpress.services.cancer_service import search_cancer, get_cancer_list
from pprint import pprint

# TODO
# from bioxpress.services.cancer_service import search_cancer, get_cancer_list

api_bp = Blueprint("api", __name__)


@api_bp.route("/getStats", methods=["GET"])
def stats():
    result = get_stats()
    return jsonify(result)


@api_bp.route("/getTranscriptData", methods=["POST"])
def transcript_data():
    input_json = request.get_json()
    result = get_transcript_data(input_json)
    return jsonify(result)


@api_bp.route("/transcriptSearch", methods=["POST"])
def search_transcript():
    print("HERE")
    input_json = request.get_json()
    pprint(input_json)
    result = transcript_search(input_json)
    return jsonify(result)


@api_bp.route("/cancerSearch", methods=["POST"])
def cancer_search():
    input_json = request.get_json()
    result = search_cancer(input_json)
    return jsonify(result)


@api_bp.route("/getCancerList", methods=["GET"])
def get_cancer_list_route():
    result = get_cancer_list()
    return jsonify(result)
