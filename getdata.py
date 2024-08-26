import os
from sqlgres import Jobs_DB
from sqlalchemy.future import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_job_data(session, jobid):
    try:
        logger.info(f"Fetching job data for job ID: {jobid}")
        query = select(Jobs_DB).filter(Jobs_DB.id == jobid)
        result = await session.execute(query)
        job = result.scalars().first()
        
        if job:
            logger.info(f"Job data retrieved successfully for job ID: {jobid}")
        else:
            logger.warning(f"No job found with job ID: {jobid}")

        return job
    except Exception as e:
        logger.error(f"Error fetching job data for job ID {jobid}: {e}")
        return None