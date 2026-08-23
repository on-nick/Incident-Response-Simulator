class Alert:

    def __init__(self, scenario, severity, message):

        self.scenario = scenario
        self.severity = severity
        self.message = message

    def to_dict(self):

        return {
            "scenario": self.scenario,
            "severity": self.severity,
            "message": self.message
        }