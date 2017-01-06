from contextlib import contextmanager
from . import exceptions as excs
from sqlalchemy.exc import DBAPIError


@contextmanager
def handle_rollback(session, msg_prefix=None):
    """
    Context manager to simplify a workflow in resources

    Parameters
    ----------
        session: SQLAlchemy
            The session to be committed with rollback handling.
        msg_prefix: str
            Prefix the reported error with the message.

    Example
    -------
    >>> with handle_rollback(db.session):
    ...     team = Team(**args)
    ...     db.session.add(team)
    ...     return team
    """
    try:
        try:
            yield
            session.commit()
        except ValueError as e:
            excs.abort(
                code=excs.http_excs.Conflict.code,
                message=prefix_message(msg_prefix, e),
            )
        except DBAPIError as e:
            excs.abort(
                code=excs.http_excs.Conflict.code,
                message=prefix_message(msg_prefix, e),
            )
    except HTTPException:
        session.rollback()
        raise


def prefix_message(p, m):
    """Prefix the message if a prefix is given

    All inputs are converted to strings
    """
    return "%s%s%s" % (p or "", " - " if p else "", m)
