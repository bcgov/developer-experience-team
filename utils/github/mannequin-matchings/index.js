import fs from "fs";
import csvParser from "csv-parser";
import dotenv from "dotenv";

dotenv.config();

const mannequinsFile = process.env.MANNEQUIN_FILE;
const mappingFile = process.env.MAPPING_FILE;
const outputFile = process.env.OUTPUT_FILE;

const mannequins = new Map();
const mapping = new Map();

function readCSVToMap(filePath, keyField, valueFields = null) {
  return new Promise((resolve, reject) => {
    const map = new Map();
    fs.createReadStream(filePath)
      .pipe(csvParser())
      .on("data", (row) => {
        const key = row[keyField]?.trim();
        if (key) {
          map.set(
            key,
            valueFields ? valueFields.map((field) => row[field]?.trim()) : row
          );
        }
      })
      .on("end", () => resolve(map))
      .on("error", (err) => reject(err));
  });
}

async function processFiles() {
  try {
    console.log("Reading mannequins file...");
    const mannequins = await readCSVToMap(mannequinsFile, "mannequin-user", [
      "mannequin-id",
    ]);

    console.log("Reading mapping file...");
    const mapping = await readCSVToMap(mappingFile, "origin", ["destination"]);

    for(var man of mannequins) {
      console.log(man);
    }

    console.log("*****************")
    for(var map of mapping) {
      console.log(map);
    }

    console.log("Processing matching records...");
    const output = [];
    for (const [mannequinUser, mannequinData] of mannequins.entries()) {
      if (mapping.has(mannequinUser)) {
        output.push({
          "mannequin-user": mannequinUser,
          "mannequin-id": mannequinData[0], // Since we stored an array
          "target-user": mapping.get(mannequinUser)[0], // Since we stored an array
        });
      }
    }

    console.log("Writing output file...");
    const outputStream = fs.createWriteStream(outputFile);
    outputStream.write("mannequin-user,mannequin-id,target-user\n");
    output.forEach((row) => {
      outputStream.write(
        `${row["mannequin-user"]},${row["mannequin-id"]},${row["target-user"]}\n`
      );
    });
    outputStream.end();

    console.log(`Output written to ${outputFile}`);
  } catch (error) {
    console.error("Error processing files:", error);
  }
}

processFiles();
