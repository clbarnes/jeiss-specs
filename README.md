# jeiss-specs

Specifications, in TSV format, of the metadata in the header of `.dat` files produced by "Jeiss" Focused Ion Beam Scanning Electron Microscopes.

## Warning

If you're thinking about using this information to write a package to read .dat files, stop!
The specs listed here, while the best documentation we have, are 3rd-party, and largely based on hearsay.

Rather than basing your image analysis workflow on this format,
consider immediately converting it to something widely-supported and self-documenting, then forgetting you ever saw the .dat.

[jeiss-convert](https://github.com/clbarnes/jeiss-convert) is a python package and CLI which uses these specs to write all information in the .dat into HDF5 groups.
Prefer this format for all your image workflow needs.

## General notes

- The value of `FileMagicNum` must be 3555587570
- Arrays are in column-major ("Fortran") order.
- Multi-byte data is in big-endian byte order, little-endian bit order.
- Date is stored as `DD/MM/YYYY`, for some reason.
- `specs/v0.tsv` is not a spec in its own right, but a core metadata common across all versions. In some cases, these fields determine the size of later metadata fields, so it's convenient to parse this first.
- The image data begins at offset 1024, and has shape (`ChanNum`, `XResolution`, `YResolution`).
- There may be a binary footer of indeterminate length, after the image data.

Some of this information is encoded in `misc.toml`.

## dtype

Field data types are encoded as 3+ characters:

- `>` for big-endian or `<` for little-endian byte order. All data types here are `>`, but it is included to be explicit. Note this is irrelevant for single-byte types (`S` and `u1`), but included anyway.
- A letter for the data type: `f`loat, `i`nteger, `u`nsigned integer, `S`tring (ASCII, right-padded with null bytes).
- An integer for how long the type is, in bytes.

This representation is based on the NumPy [Array Interface](https://numpy.org/doc/stable/reference/arrays.interface.html#object.__array_interface__)'s typestrs.

Some `>u1` fields represent booleans, where 0 is False and anything else is True.

### Enums

Some integer fields represent enums.
`enums/${FIELD_NAME}.tsv` enumerate the integer values and the enums they represent.

## shape

`0` represents a single element (where `1` would represent a 1-length array).
For multidimensional arrays, the length of each dimension is separated by a comma.
In some versions, the shape depends on the value of an earlier field: in that case, the name of the field is used instead of an integer.

## Example files

### Public images

For testing purposes, `example_files.tsv` lists publicly-accessible URLs to `.dat` files for specific versions.

The TSV lists the version number, the hex digest of the MD5 hashsum of the file, and a public URL to the file.

### Example metadata

The `example_metadata` directory contains truncated `.dat` files,
containing only the metadata portion, again for testing purposes.

## Contributing

To add a new Jeiss .dat specification:

1. Create a new specification TSV in the `specs` dir (possibly by copying the TSV for the version it's based on)
2. Update it to reflect the contents of the new version
    - You can do this in most spreadsheet editors, like [LibreOffice Calc](https://www.libreoffice.org/) or Microsoft Excel
3. If you introduce or modify any enums, update the TSVs in the `enums` directory
4. Make an example image pubicly available and add it to the `example_files.tsv`
    - MD5 digests can be calculated with `md5sum $YOUR_DAT_PATH`.
5. Include just the metadata portion of the image in `example_metadata`
    - Files can be truncated with `head -c 1024 $YOUR_DAT_PATH > truncated.dat`
6. Ensure all the TSV files are correctly formatted using `scripts/tsvfmt.py enums specs example_files.tsv`
7. Raise a pull request to add your changes to the mainline repository

## Attribution

These specs were generated from Davis Bennett's [fibsem-tools](https://github.com/janelia-cosem/fibsem-tools).
Thanks also to Mark Kittisopikul for his work on sanitising the format,
and to Shan Xu and the Hess lab for their creation of the Jeiss FIBSEM.
