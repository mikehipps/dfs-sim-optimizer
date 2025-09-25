name: Bug report
description: Something broke or behaves wrong
title: "[bug] "
labels: ["bug"]
body:
  - type: textarea
    id: observed
    attributes:
      label: Observed behavior
      placeholder: What happened?
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
      placeholder: What should have happened?
    validations:
      required: true
