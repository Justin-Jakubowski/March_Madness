library(readr)
library(dplyr)
library(purrr)
library(tools)
library(pdftools)

# Path to folder with CSVs
kaggle_path <- "Kaggle/"

# List all CSV files in that folder
csv_files <- list.files(path = kaggle_path, pattern = "*.csv", full.names = TRUE)

# Read them all into a named list of dataframes
csv_list <- map(csv_files, ~read_csv(.x, show_col_types = FALSE))
names(csv_list) <- file_path_sans_ext(basename(csv_files))

# Print column names of the 'Z Rating' file before merging
if ("Z Rating" %in% names(csv_list)) {
  cat("Column names in 'Z Rating' file before merging:\n")
  print(colnames(csv_list[["Z Rating"]]))
}

# Exclude data frames without both 'TEAM' and 'YEAR' columns
csv_list <- csv_list[sapply(csv_list, function(df) all(c("TEAM", "YEAR") %in% colnames(df)))]

# Remove duplicate TEAM-YEAR rows in each data frame
csv_list <- lapply(csv_list, function(df) df[!duplicated(df[c("TEAM", "YEAR")]), ])

# Remove suffixes and duplicate columns from column names in each data frame before merging
csv_list <- lapply(csv_list, function(df) {
  colnames(df) <- gsub("\\..*$", "", colnames(df))
  df <- df[, !duplicated(colnames(df))]
  df
})

# Diagnostic: Print file names, row counts, and first few rows
for (name in names(csv_list)) {
  cat("File:", name, "- Rows:", nrow(csv_list[[name]]), "\n")
  print(head(csv_list[[name]]))
}

# Only merge if there are data frames left
if (length(csv_list) > 0) {
  master_df <- reduce(csv_list, function(x, y) full_join(x, y, by = c("TEAM", "YEAR")))
  # Remove suffixes from column names in merged data frame
  colnames(master_df) <- gsub("\\..*$", "", colnames(master_df))
  # Keep only the first occurrence of each column name
  master_df <- master_df[, !duplicated(colnames(master_df))]
  print(head(master_df))
  print(colnames(master_df))
  # Check for duplicate base column names (ignoring suffixes)
  base_names <- gsub("\\..*$", "", colnames(master_df))
  dup_names <- base_names[duplicated(base_names)]
  cat("Duplicate base column names (ignoring suffixes):\n")
  print(unique(dup_names))
  # Save merged data to CSV
  write.csv(master_df, "merged_march_madness.csv", row.names = FALSE)
  cat("Merged data saved to merged_march_madness.csv\n")
} else {
  cat("No CSV files with both 'TEAM' and 'YEAR' columns found.\n")
}

# Example: Create a template for a 64-team NCAA bracket
# You can fill in the actual team names and seeds manually or from a CSV
bracket_template <- data.frame(
  Region = rep(c("East", "West", "South", "Midwest"), each = 16),
  Seed = rep(1:16, times = 4),
  Team = NA_character_,
  Opponent = NA_character_,
  stringsAsFactors = FALSE
)

# Print the bracket template
print(bracket_template)

# To fill in teams and seeds, you can use:
# bracket_template$Team <- c("Team1", "Team2", ..., "Team64")
# bracket_template$Opponent <- c("Opponent1", "Opponent2", ..., "Opponent64")

# You can also read in a CSV with bracket info and merge with your stats
# bracket_template <- read.csv("your_bracket_file.csv")

# Example: Extract and parse bracket text from PDF using pdftools
if (!requireNamespace("pdftools", quietly = TRUE)) {
  install.packages("pdftools")
}
library(pdftools)

# Path to your PDF file
pdf_file <- "2023 bracket.pdf"

# Extract text from the PDF
pdf_text <- pdf_text(pdf_file)

# Print the text from the first page for inspection
cat(pdf_text[1])

# Extract lines from the PDF text
lines <- unlist(strsplit(pdf_text[1], "\n"))

# Improved region assignment for bracket parsing
region_keywords <- c("SOUTH", "MIDWEST", "EAST", "WEST")
current_region <- NA
bracket_entries <- list()

for (i in seq_along(lines)) {
  # Update current region if a region keyword is found
  region_found <- region_keywords[region_keywords %in% unlist(strsplit(lines[i], "[[:space:]]+"))]
  if (length(region_found) > 0) {
    current_region <- region_found[1]
  }
  # Extract all seed-team pairs from the line
  matches <- gregexpr("([1-9][0-6]?)[[:space:]]+([A-Za-z .'/&-]+)", lines[i])
  if (matches[[1]][1] != -1) {
    for (j in seq_along(matches[[1]])) {
      match_str <- regmatches(lines[i], matches)[[1]][j]
      seed_num <- as.integer(sub("^([1-9][0-6]?).*", "\\1", match_str))
      team <- sub("^[1-9][0-6]?[[:space:]]+", "", match_str)
      bracket_entries[[length(bracket_entries) + 1]] <- data.frame(Region = current_region, Seed = seed_num, Team = team, stringsAsFactors = FALSE)
    }
  }
}

# Combine all entries into a data frame
bracket_df <- do.call(rbind, bracket_entries)

# Print the parsed bracket data frame
print(bracket_df)
