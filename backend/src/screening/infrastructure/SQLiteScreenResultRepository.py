import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.domain.StockCode import StockCode
from src.shared.domain.ScoreTier import tier_from_score
from src.llm.domain.Analysis import ScoreCard, StockAnalysis, AnalysisRepository
from src.screening.infrastructure.ScreeningORM import ScreenTaskModel, ScreenResultModel


class SQLiteScreenResultRepository(AnalysisRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, analysis: StockAnalysis) -> None:
        model = ScreenResultModel(
            stock_code=str(analysis.stock_code),
            stock_name=analysis.stock_name,
            dimension_scores=json.dumps(analysis.score_card.dimension_scores, ensure_ascii=False),
            composite_score=analysis.score_card.composite_score,
            tier=analysis.score_card.tier.value,
            reasoning=analysis.score_card.reasoning,
        )
        self._session.add(model)
        await self._session.commit()

    async def find_by_code(self, code: StockCode, limit: int = 10) -> list[StockAnalysis]:
        result = await self._session.execute(
            select(ScreenResultModel)
            .where(ScreenResultModel.stock_code == str(code))
            .order_by(ScreenResultModel.created_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        analyses: list[StockAnalysis] = []
        for r in rows:
            card = ScoreCard(
                dimension_scores=json.loads(r.dimension_scores),
                composite_score=r.composite_score,
                tier=tier_from_score(r.composite_score),
                reasoning=r.reasoning,
            )
            analyses.append(StockAnalysis(
                id=str(r.id),
                stock_code=StockCode(r.stock_code),
                stock_name=r.stock_name,
                score_card=card,
            ))
        return analyses

    async def save_task(self, universe: str, dimensions: list[str]) -> int:
        model = ScreenTaskModel(
            universe=universe,
            dimensions=json.dumps(dimensions),
            status="running",
        )
        self._session.add(model)
        await self._session.commit()
        return model.id

    async def update_task(self, task_id: int, status: str, result_count: int = 0) -> None:
        result = await self._session.execute(
            select(ScreenTaskModel).where(ScreenTaskModel.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.status = status
            task.result_count = result_count
            await self._session.commit()

    async def get_tasks(self, limit: int = 20) -> list[dict]:
        result = await self._session.execute(
            select(ScreenTaskModel).order_by(ScreenTaskModel.created_at.desc()).limit(limit)
        )
        rows = result.scalars().all()
        return [
            {"id": r.id, "universe": r.universe, "status": r.status,
             "result_count": r.result_count, "created_at": str(r.created_at)}
            for r in rows
        ]
