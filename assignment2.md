# Assignment 2

## Intro

You can find stackholder request in another attached file.

## Suggeted API endpoints

- POST /habits — Create habit
- GET /habits — List all habits
- GET /habits/{id} — Get single habit
- PUT /habits/{id} — Update habit
- DELETE /habits/{id} — Delete habit
- POST /habits/{id}/subhabits — Add sub-habit
- POST /habits/{id}/logs — Record progress
- GET /habits/{id}/logs — List logs
- GET /habits/{id}/stats — Get statistics

## Linting/formatting

- Format and lint your code using `ruff`
- Check your static types with `mypy`

You can find configuration for these tools in playground project developed during sessions.
Alternatively you can adopt pyproject.toml form [this](https://github.com/MadViper/nand2tetris-starter-py/blob/main/pyproject.toml) project.

## Grading

We will not grade solutions:
  - without decomposition
  - with needlessly long methods or classes
  - with code duplications
In all these cases you will automatically get 0% so, we sincerely ask you to 
not make a mess of your code and not put us in an awkward position.

- 20%: It is tested!
- 20%: It is easy to change.
- 20%: It demonstrates an understanding of design patterns.
- 20%: It demonstrates an understanding of Restful API and S.O.L.I.D principles.
- 20%: Linting/formatting.

## Disclaimer

We reserve the right to resolve ambiguous requirements (if any) as we see fit just like a real-life stakeholder would. So, do not assume anything, ask for clarifications.
