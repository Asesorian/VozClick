"""DictaFlow — Dashboard Flask (historial transcripciones)"""
import logging
import threading
from flask import Flask, render_template, request, redirect, url_for

logger = logging.getLogger(__name__)


def create_dashboard(db, port: int) -> threading.Thread:
    app = Flask(__name__, template_folder="templates")

    @app.route("/")
    def index():
        page = int(request.args.get("page", 1))
        search = request.args.get("q", "")
        results, total = db.get_transcriptions(page=page, search=search)
        total_pages = max(1, (total + 49) // 50)
        return render_template(
            "index.html",
            transcriptions=results,
            page=page,
            total_pages=total_pages,
            total=total,
            search=search,
        )

    @app.route("/delete/<int:id>", methods=["POST"])
    def delete(id):
        db.delete_transcription(id)
        page = request.args.get("page", 1)
        search = request.args.get("q", "")
        return redirect(url_for("index", page=page, q=search))

    @app.route("/clear", methods=["POST"])
    def clear():
        db.clear_all_transcriptions()
        return redirect(url_for("index"))

    def run():
        try:
            app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
        except OSError as e:
            logger.warning(f"Dashboard could not start on port {port}: {e}")

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t
