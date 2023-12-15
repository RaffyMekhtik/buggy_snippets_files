def _create_render_start_handler(name, gcode=None):
	def f(movie):
		global _job_lock

		with _job_lock:
			global current_render_job
			event_payload = {"gcode": gcode if gcode is not None else "unknown",
			                 "movie": movie,
			                 "movie_basename": os.path.basename(movie)}
			current_render_job = dict(prefix=name)
			current_render_job.update(event_payload)
		eventManager().fire(Events.MOVIE_RENDERING, event_payload)
	return f