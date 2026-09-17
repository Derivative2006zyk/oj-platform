class EventNames:
    """Event name constants for the event bus.

    Naming convention: domain.action
    See project overview chapter 9.4 for the full channel list.
    """

    # Problem plugin
    PROBLEM_CREATED = "problem.created"
    PROBLEM_UPDATED = "problem.updated"
    PROBLEM_DELETED = "problem.deleted"

    # Image
    IMAGE_UPLOADED = "image.uploaded"

    # User plugin
    USER_REGISTERED = "user.registered"
    USER_LOGGED_IN = "user.logged_in"

    # Judge plugin
    SUBMISSION_CREATED = "submission.created"
    SUBMISSION_JUDGED = "submission.judged"

    # OCR plugin
    OCR_COMPLETED = "ocr.completed"

    # AI plugin
    AI_COMPLETED = "ai.completed"