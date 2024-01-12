from __future__ import annotations

from math import tanh

from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from pwncore.models.user import Team

__all__ = (
    "Problem",
    "Hint",
    "SolvedProblem",
    "ViewedHint",
    "BaseProblem_Pydantic",
    "Hint_Pydantic",
)


class BaseProblem(Model):
    name = fields.TextField()
    description = fields.TextField()
    # both tables inherit points, for pre-event points means coins
    points = fields.IntField()
    author = fields.TextField()


class Problem(BaseProblem):
    image_name = fields.TextField()
    image_config: fields.Field[dict[str, list]] = fields.JSONField(
        null=True
    )  # type: ignore[assignment]

    mi = fields.IntField(default=100)  # Arbitrary meaning full defaults
    ma = fields.IntField(default=600)

    hints: fields.ReverseRelation[Hint]

    class PydanticMeta:
        exclude = ["image_name", "image_config"]

    async def _solves(self) -> int:
        return await SolvedProblem.filter(problem=self).count()

    async def update_points(self) -> None:
        self.points = round(
            self.mi + (self.ma - self.mi) * (1 - tanh((await self._solves()) / 125))
        )
        await self.save()


class Hint(Model):
    id = fields.IntField(pk=True)
    order = fields.SmallIntField()  # 0, 1, 2
    problem: fields.ForeignKeyRelation[Problem] = fields.ForeignKeyField(
        "models.Problem", related_name="hints"
    )
    text = fields.TextField()

    class Meta:
        ordering = ("order",)


class SolvedProblem(Model):
    team: fields.ForeignKeyRelation[Team] = fields.ForeignKeyField(
        "models.Team", related_name="solved_problem"
    )
    problem: fields.ForeignKeyRelation[Problem] = fields.ForeignKeyField(
        "models.Problem"
    )
    solved_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        unique_together = (("team", "problem"),)


class ViewedHint(Model):
    team: fields.ForeignKeyRelation[Team] = fields.ForeignKeyField(
        "models.Team", related_name="viewedhints"
    )
    hint: fields.ForeignKeyRelation[Hint] = fields.ForeignKeyField(
        "models.Hint",
    )

    class Meta:
        unique_together = (("team", "hint"),)


BaseProblem_Pydantic = pydantic_model_creator(BaseProblem)
Hint_Pydantic = pydantic_model_creator(Hint)
