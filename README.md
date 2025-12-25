# stuff i consumed

[consumed.ethanpinedaa.dev](https://consumed.ethanpinedaa.dev)

every hour, a new static website is generated. we add the following if anything new has been created: 

- audio (music): which list which songs i listened too. this is connected to my apple music
- text: any article/piece of text that i found interesting
- video: any videos that are interesting
- physical: anything physical that i consumed (food)
- place: any place that i visited

everything from the website gets added either through an automation (at least only for apple music) or through some other medium. 

for example, i have created apple shortcuts to use the action button on my iphone to help with adding stuff to the site. 

i also created a personal extension for both firefox and chrome to add stuff while i am browsing the web

everything is persisted in a postgres db hosted by railway. the api (python server) is also hosted on railway for $5 a month. 

images are stored using cloudfare r2 and cloudfare workers help with the fetching and displaying of the images. 

feel free to copy, this is more so more for personal use than anything
