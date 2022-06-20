from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from domain import model
from adapters import orm, repository
from service_layer import services

"""
플라스크 앱의 책임은 표준적인 웹 기능일 뿐이다. 요청 전 상태를 관리하고 POST 파라미터로부터 정보를 파싱하며
상태 코드를 응답하고 JSON을 처리한다. 그 외 모든 오케스트레이션 로직은 유스 케이스/서비스 계층에 들어가고,
도메인 로직은 도메인에 그대로 남는다.
"""

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    line = model.OrderLine(
        request.json["orderid"],
        request.json["sku"],
        request.json["qty"],
    )
    try:
        batchref = services.allocate(line, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"batchref": batchref}), 201


@app.route("/deallocate", methods=["POST"])
def deallocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    line = model.OrderLine(
        request.json["orderid"],
        request.json["sku"],
        request.json["qty"],
    )
    services.deallocate(line, repo, session)
    return 200
