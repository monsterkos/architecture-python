from datetime import datetime
from flask import Flask, jsonify, request

from src.allocation.domain import model
from src.allocation.adapters import orm
from src.allocation.service_layer import services
from src.allocation.service_layer.unit_of_work import SqlAlchemyUnitOfWork

"""
플라스크 앱의 책임은 표준적인 웹 기능일 뿐이다. 요청 전 상태를 관리하고 POST 파라미터로부터 정보를 파싱하며
상태 코드를 응답하고 JSON을 처리한다. 그 외 모든 오케스트레이션 로직은 유스 케이스/서비스 계층에 들어가고,
도메인 로직은 도메인에 그대로 남는다.
"""

app = Flask(__name__)
orm.start_mappers()


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        batchref = services.allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
            SqlAlchemyUnitOfWork(),
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"batchref": batchref}), 201


@app.route("/deallocate", methods=["POST"])
def deallocate_endpoint():
    services.deallocate(
        request.json["orderid"],
        request.json["sku"],
        request.json["qty"],
        SqlAlchemyUnitOfWork(),
    )
    return "OK", 200


@app.route("/batch", methods=["POST"])
def add_batch():
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    services.add_batch(
        request.json["ref"],
        request.json["sku"],
        request.json["qty"],
        eta,
        SqlAlchemyUnitOfWork(),
    )
    return "OK", 201
