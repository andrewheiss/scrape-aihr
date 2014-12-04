library(plyr)
library(dplyr)
library(tidyr)
library(lubridate)
library(ggplot2)
library(grid)
library(rath)
library(rgeos)
library(maptools)

aihr.full <- read.csv("aihr-full.csv", na.strings="", stringsAsFactors=FALSE)
tz = "EST"

# Load manually created dictionary CSV and create a named list to be used in revalue
country.dict <- read.csv("country_names.csv", stringsAsFactors=FALSE)
country.replace <- country.dict$english_name
country.replace <- setNames(country.replace, country.dict$original_name)

# Load country name dictionary
countries <- read.csv("countries.csv", na.strings="")

# Clean up data
# Remove duplicates (ignoring id and date_added)
aihr.clean <- aihr.full[!duplicated(aihr.full[,-1:-2]), ] %>%  
  mutate(date_of_creation = revalue(date_of_creation, 
                                    c("0208-04-01" = "2008-04-01",
                                      "0000-00-00" = NA))) %>%
  mutate(country = revalue(country, country.replace)) %>%
  mutate(country = strsplit(country, " \\| ")) %>%  # Split multiple countries into lists
  unnest(country) %>%  # Magic tidyr function to make multiple rows based on listed cells
  left_join(countries, by="country") %>%  # Add ISO and FIPS codes
  mutate(date_added = ymd_hms(date_added, tz=tz),
         date_of_creation = ymd(date_of_creation, tz=tz)) %>%
  mutate(ngo_id = factor(ngo_id), 
         latin_name = factor(latin_name),
         arabic_name = factor(arabic_name),
         country = factor(country),  # Make a factor initially
         country = factor(country,  # Reorder by frequency
                          levels=levels(country)[rev(order(tabulate(country)))],
                          ordered=TRUE),
         country.rev = factor(country, levels=rev(levels(country))),
         governorate = factor(governorate))


# Remove entries with missing countries
plot.data <- aihr.clean[!is.na(aihr.clean$country.rev), ]
# plot.data <- na.omit(aihr.clean[, c("country.rev", "ngo_id")])  # Alternative

p <- ggplot(plot.data, aes(x=country.rev)) 
p1 <- p + geom_bar() + coord_flip() + theme_ath() + 
  labs(x=NULL, y="Count")
p1

ggsave(p1, filename="ngo_count.png", width=7, height=5)

# Load map information
world.map <- readShapeSpatial("maps/TM_WORLD_BORDERS_SIMPL-0.3.shp")
world.ggmap <- ggplot2::fortify(world.map, region = "ISO3")

countries.freq <- aihr.clean %>%
  select(country)


countries.plot <- data.frame(as.list(table(aihr.clean$country))) %>% 
  gather(country, freq) %>%
  mutate(country = gsub("\\.", " ", country)) %>%  # table() adds .s for spaces
  left_join(countries, by="country")

theme_blank_map <- theme(panel.background = element_rect(fill="white"),
                         panel.grid.major = element_blank(),
                         panel.grid.minor = element_blank(),
                         axis.line=element_blank(),
                         axis.text.x=element_blank(),
                         axis.text.y=element_blank(),
                         axis.ticks=element_blank(),
                         axis.title.x=element_blank(),
                         axis.title.y=element_blank())

ngo.map <- ggplot(countries.plot, aes(map_id=ISO3)) +
  geom_map(aes(fill=freq), map=world.ggmap, colour="black", size=0.25) +
  expand_limits(x=world.ggmap$long, y=world.ggmap$lat) +
  scale_fill_gradient(high="#ff7f00", low="#fff7bc", na.value="grey",
                      guide="colorbar", name="# of NGOs") +
  coord_map(xlim=c(-20,60), ylim=c(-5, 55)) +
  theme_blank_map + theme(legend.key.width=unit(0.55, "line"))

ggsave(ngo.map, filename="ngo_map.pdf", width=7, height=4)

gtranslate.cost <- function(n) {
  20 * (n / 1000000)
}

# Whole thing
sum(gtranslate.cost(nchar(aihr.clean)))

# One column
sum(gtranslate.cost(nchar(aihr.clean$missions_and_goals)))
