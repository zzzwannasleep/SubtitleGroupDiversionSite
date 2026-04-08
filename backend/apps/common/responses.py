from rest_framework.response import Response


def success_response(data=None, message: str = "ok", status_code: int = 200):
    return Response({"success": True, "data": data, "message": message}, status=status_code)
