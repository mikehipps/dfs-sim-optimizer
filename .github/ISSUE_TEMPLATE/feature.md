name: Feature request
description: Request a small, shippable improvement
title: "[feat] "
labels: ["feat"]
body:
  - type: textarea
    id: goal
    attributes:
      label: Goal
      description: What outcome you want (e.g., "Enable DK roster sampling")
      placeholder: Clear, one-paragraph goal
    validations:
      required: true
  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance criteria
      description: Bullet list of what "done" means
      placeholder: "- API does X\n- UI shows Y"
    validations:
      required: true
