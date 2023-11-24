from markdown.extensions import Extension


class WikiJanitorExtension(Extension):
	def extendMarkdown(self, md):
		# enable processing of markdown content within <details> tag
		md.block_level_elements.remove('details')


def makeExtension(*args, **kwargs):
	return WikiJanitorExtension(*args, **kwargs)
